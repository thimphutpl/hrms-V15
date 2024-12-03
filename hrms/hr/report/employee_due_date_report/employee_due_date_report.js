// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Due Date Report"] = {
	"filters": [
		{
			"fieldname": "uinput",
			"label": ("Options"),
			"fieldtype": "Select",
			"width": "80",
			"options": [
				 { "value": "promotion_due_date", "label": __("Promotion Due Date") },
				 { "value": "contract_end_date", "label": __("Contact Renew Date") },
				 { "value": "date_of_retirement", "label": __("Retirement Date") },
			],
			"reqd": 1
		},

		{
			"fieldname": "branch",
			"label": ("Branch"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Branch",
		},
		{
			"fieldname":"from_date",
			"label": ("From Date"),
			"fieldtype": "Date",
			"width": "80",

		},
		{
			"fieldname":"to_date",
			"label": ("To Date"),
			"fieldtype": "Date",
			"width": "80",
		},

	]
}