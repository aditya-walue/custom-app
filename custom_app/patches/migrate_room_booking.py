import frappe
from frappe.modules.import_file import import_file_by_path
import os

def execute():
    # 1. Update page module to Custom app if it exists
    if frappe.db.exists('Page', 'room-booking'):
        frappe.db.set_value('Page', 'room-booking', 'module', 'Custom app')
        frappe.db.commit()
        
    # 2. Force import the page from custom_app package directory
    app_path = frappe.get_app_path('custom_app')
    page_json_path = os.path.join(app_path, 'custom_app', 'page', 'room_booking', 'room_booking.json')
    if os.path.exists(page_json_path):
        import_file_by_path(page_json_path, force=True)
        frappe.db.commit()
        
    # 3. Force import the doctypes Meeting room and Meeting Room Booking from custom_app
    for doctype in ['Meeting room', 'Meeting Room Booking']:
        if frappe.db.exists('DocType', doctype):
            frappe.db.set_value('DocType', doctype, 'module', 'Custom app')
            frappe.db.commit()
            
        dt_json_path = os.path.join(app_path, 'custom_app', 'doctype', frappe.scrub(doctype), f"{frappe.scrub(doctype)}.json")
        if os.path.exists(dt_json_path):
            import_file_by_path(dt_json_path, force=True)
            frappe.db.commit()

    # 4. Force import the workspace Meeting from custom_app
    workspace_json_path = os.path.join(app_path, 'custom_app', 'workspace', 'meeting', 'meeting.json')
    if os.path.exists(workspace_json_path):
        if frappe.db.exists('Workspace', 'Meeting'):
            frappe.delete_doc('Workspace', 'Meeting', force=True)
            frappe.db.commit()
        import_file_by_path(workspace_json_path, force=True)
        frappe.db.commit()

