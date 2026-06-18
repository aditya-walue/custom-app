# Copyright (c) 2026, Code Yard Private Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import timedelta


def _fmt_time(t):
    """Ensure time value is zero-padded HH:MM:SS string."""
    if isinstance(t, timedelta):
        total = int(t.total_seconds())
        h, remainder = divmod(total, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    s = str(t)
    # Pad single-digit hours: "9:00:00" -> "09:00:00"
    parts = s.split(":")
    if len(parts) >= 2 and len(parts[0]) == 1:
        s = "0" + s
    return s


@frappe.whitelist()
def get_bookings(start, end, room=None):
    """Fetch bookings for the calendar view.

    Args:
        start: ISO date string (start of calendar range)
        end: ISO date string (end of calendar range)
        room: Optional room filter

    Returns:
        List of booking dicts with FullCalendar-compatible fields
    """
    filters = {
        "date": ["between", [start[:10], end[:10]]],
        "status": "Booked",
    }
    if room:
        filters["room"] = room

    bookings = frappe.get_all(
        "Meeting Room Booking",
        filters=filters,
        fields=[
            "name", "room", "date", "from_time", "to_time",
            "booked_by", "purpose", "status", "color",
        ],
        order_by="date asc, from_time asc",
    )

    for b in bookings:
        b["full_name"] = (
            frappe.db.get_value("User", b["booked_by"], "full_name")
            or b["booked_by"]
        )
        b["from_time"] = _fmt_time(b["from_time"])
        b["to_time"] = _fmt_time(b["to_time"])
        b["date"] = str(b["date"])

    return bookings


@frappe.whitelist()
def create_booking(room, date, from_time, to_time, purpose=None):
    """Create a new meeting room booking.

    Overlap validation is handled by the DocType controller.
    """
    doc = frappe.get_doc(
        {
            "doctype": "Meeting Room Booking",
            "room": room,
            "date": date,
            "from_time": from_time,
            "to_time": to_time,
            "purpose": purpose or "",
            "booked_by": frappe.session.user,
            "status": "Booked",
        }
    )
    doc.insert()
    frappe.db.commit()

    return {
        "name": doc.name,
        "message": _("Room {0} booked successfully").format(room),
    }


@frappe.whitelist()
def cancel_booking(booking_name):
    """Cancel a meeting room booking.

    Only the person who booked or System Manager can cancel.
    """
    doc = frappe.get_doc("Meeting Room Booking", booking_name)

    if (
        doc.booked_by != frappe.session.user
        and "System Manager" not in frappe.get_roles()
    ):
        frappe.throw(
            _("You can only cancel your own bookings"),
            frappe.PermissionError,
        )

    doc.status = "Cancelled"
    doc.save()
    frappe.db.commit()

    return {"name": doc.name, "message": _("Booking cancelled")}
