// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Loan Report"] = {
	"filters": [
	{
		"fieldname": "fiscal_year",
		"label": "Fiscal Year",
		"fieldtype": "Link",
		"options": "Fiscal Year",
		"reqd": 1,
				"default": function() {
					// Get current fiscal year based on today's date
					var today = frappe.datetime.get_today();
					var fiscal_year = frappe.sys_defaults.fiscal_year;
					
					// Or use user's default fiscal year
					var user_fiscal_year = frappe.defaults.get_user_default("fiscal_year");
					return user_fiscal_year || fiscal_year;
				}()

	},
	{
				"fieldname": "month",
				"label": "Month",
				"fieldtype": "Select",
				"options": "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
				"default": ""
			},
	{
		"fieldname": "employee",
		"label": "Employee",
		"fieldtype": "Link",
		"options": "Employee"
	},
	{
		"fieldname": "employee_name",
		"label": "Employee Name",
		"fieldtype": "Data"
	},
	{
		"fieldname": "company",
		"label": "Company",
		"fieldtype": "Link",
		"options": "Company",
		
	}
]
};
