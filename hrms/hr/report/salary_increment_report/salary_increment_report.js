// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Increment Report"] = {
	"filters": [
		{
			"fieldname": "docstatus",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": [
				{ "label": "All", "value": "" },
				{ "label": "Draft", "value": "0" },
				{ "label": "Submitted", "value": "1" },
				{ "label": "Cancelled", "value": "2" }
			]

		},	
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
		},
		{
			"fieldname":"fiscal_year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
		},
		{
			"fieldname":"month",
			"label": __("Month"),
			"fieldtype": "Link",
			"options": "Month",
		}

	]
};
