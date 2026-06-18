# Copyright (c) 2026, Code Yard Private Limited and contributors
# For license information, please see license.txt

import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time

# Linked master DocType holding the rooms (e.g. 3A, 3B). It is expected to
# already exist on the site; see README for the dependency.
ROOM_DOCTYPE = "Meeting room"

# Stable palette used to auto-assign a color per room (deterministic by name).
ROOM_COLOR_PALETTE = [
    "#4F46E5",  # Indigo
    "#f59e0b",  # Amber
    "#10b981",  # Emerald
    "#ef4444",  # Red
    "#8b5cf6",  # Violet
    "#0ea5e9",  # Sky
    "#ec4899",  # Pink
    "#14b8a6",  # Teal
]
DEFAULT_ROOM_COLOR = "#6366f1"


class MeetingRoomBooking(Document):
    def validate(self):
        self.validate_times()
        self.check_overlap()
        self.set_datetime_fields()
        self.set_color()

    def validate_times(self):
        """Ensure from_time is strictly before to_time.

        Compare as time objects, never as strings. Frappe returns Time fields
        as datetime.timedelta after a DB read, and str(timedelta) is not
        zero-padded ("9:00:00"), so a string compare wrongly ranks
        "9:00:00" >= "10:00:00" and blocks editing/cancelling morning slots.
        """
        if self.from_time and self.to_time:
            if get_time(self.from_time) >= get_time(self.to_time):
                frappe.throw(_("From Time must be before To Time"))

    def check_overlap(self):
        """Prevent double-booking the same room at overlapping times.

        Two intervals [A_start, A_end) and [B_start, B_end) overlap iff
        A_start < B_end AND B_start < A_end.
        """
        if self.status == "Cancelled":
            return

        # Serialize concurrent bookings for the same room. Locking the room
        # master row makes the check-and-insert atomic, closing the
        # double-booking race where two requests both pass the check below.
        if self.room and frappe.db.exists("DocType", ROOM_DOCTYPE):
            frappe.db.get_value(ROOM_DOCTYPE, self.room, "name", for_update=True)

        overlapping = frappe.db.sql(
            """
            SELECT name, room, from_time, to_time, booked_by
            FROM `tabMeeting Room Booking`
            WHERE room = %(room)s
              AND date = %(date)s
              AND name != %(name)s
              AND status = 'Booked'
              AND from_time < %(to_time)s
              AND to_time > %(from_time)s
            LIMIT 1
            """,
            {
                "room": self.room,
                "date": self.date,
                "name": self.name or "",
                "from_time": self.from_time,
                "to_time": self.to_time,
            },
            as_dict=True,
        )

        if overlapping:
            b = overlapping[0]
            frappe.throw(
                _("Room {0} is already booked from {1} to {2} by {3}").format(
                    frappe.bold(self.room), b.from_time, b.to_time, b.booked_by
                ),
                title=_("Room Not Available"),
            )

    def set_datetime_fields(self):
        """Compute starts_on / ends_on for Calendar View compatibility."""
        if self.date and self.from_time:
            self.starts_on = f"{self.date} {self.from_time}"
        if self.date and self.to_time:
            self.ends_on = f"{self.date} {self.to_time}"

    def set_color(self):
        """Auto-assign a stable color per room for the calendar."""
        if not self.color:
            self.color = get_room_color(self.room)


def get_room_color(room: str | None) -> str:
    """Resolve a display color for a room.

    Prefers an explicit `color` field on the Meeting room master if present;
    otherwise derives a deterministic color from the room name so every room
    (including ad-hoc named ones) gets a consistent color with no hardcoded map.
    """
    if not room:
        return DEFAULT_ROOM_COLOR

    if frappe.db.exists("DocType", ROOM_DOCTYPE):
        meta = frappe.get_meta(ROOM_DOCTYPE)
        if meta.has_field("color"):
            master_color = frappe.db.get_value(ROOM_DOCTYPE, room, "color")
            if master_color:
                return master_color

    digest = hashlib.md5(room.encode("utf-8")).hexdigest()
    return ROOM_COLOR_PALETTE[int(digest, 16) % len(ROOM_COLOR_PALETTE)]
