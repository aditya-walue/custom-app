// Calendar View configuration for Meeting Room Booking list view
// This enables the built-in Frappe calendar when viewing the DocType list
frappe.views.calendar["Meeting Room Booking"] = {
	field_map: {
		start: "starts_on",
		end: "ends_on",
		id: "name",
		title: "purpose",
		color: "color",
	},
	gantt: false,
	filters: [
		{
			fieldtype: "Link",
			fieldname: "room",
			options: "Meeting room",
			label: __("Room"),
		},
	],
	get_events_method: "frappe.desk.calendar.get_events",
};
