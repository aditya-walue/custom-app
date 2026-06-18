# Copyright (c) 2026, Code Yard Private Limited and contributors
# For license information, please see license.txt

from frappe.model.document import Document


# NOTE: class name must be the DocType name with spaces removed and case
# preserved (frappe get_controller: doctype.replace(" ", "")), so the
# DocType "Meeting room" maps to `Meetingroom`, not `MeetingRoom`.
class Meetingroom(Document):
    pass
