// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Salary Increment"] = {
	"filters": [
	{
                        "fieldname": "uinput",
                        "label": ("Status"),
                        "fieldtype": "Select",
                        "width": "120",
                        "options":["All", "Draft", "Submitted"],
                        "width": "100",
                        "reqd": 1
          },

	{		
			"fieldname":"branch",
			"label": ("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": "100"
		},

	{
                        "fieldname":"fiscal_year",
                        "label": ("Fiscal Year"),
                        "fieldtype": "Link",
                        "options": "Fiscal Year",
                        "width": "100"
                },
	{
                        "fieldname":"month",
                        "label": ("Month"),
                        "fieldtype": "Select",
                        "options": [" ", "January", "July"],
                        "width": "100"
                }

	]
}
