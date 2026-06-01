// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt


frappe.query_reports["Monthly Salary Register Summary"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "fiscal_year",
			label: __("Fiscal Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [
				"",
				"Jan",
				"Feb",
				"Mar",
				"Apr",
				"May",
				"Jun",
				"Jul",
				"Aug",
				"Sep",
				"Oct",
				"Nov",
				"Dec"
			],
			reqd: 1
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch"
		},		
		
		{
			fieldname: "only_slipped_employees",
			label: __("Only Slipped Employees"),
			fieldtype: "Check",
			default: 0,
			description: __("Show only employees from Salary Slip register.")
		},
		{
			fieldname: "only_others",
			label: __("Only Others"),
			fieldtype: "Check",
			default: 0,
			description: __("Show only Musterroll/OAP/Operator/GFG/DFG from MR Payment and Consultant JE if account is selected.")
		},
		{
			fieldname: "hr_cost_dashboard",
			label: __("HR Cost Dashboard"),
			fieldtype: "Check",
			default: 0,
			description: __("Show branch-wise Monthly, Daily and Hourly HR Cost dashboard.")
		},
		{
			fieldname: "show_detail",
			label: __("Show Detail Rows"),
			fieldtype: "Check",
			default: 0,
			description: __("If ticked, the report will show employee-wise rows before summary rows.")
		}
	]
};