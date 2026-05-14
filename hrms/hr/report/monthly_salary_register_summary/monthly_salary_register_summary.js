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
			fieldname: "employment_type",
			label: __("Employment Type"),
			fieldtype: "Link",
			options: "Employment Type"
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			get_query: function () {
				let company = frappe.query_report.get_filter_value("company");

				return {
					filters: {
						company: company,
						is_group: 0
					}
				};
			}
		},
		{
			fieldname: "consultant_account",
			label: __("Consultant Expense Account"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				let company = frappe.query_report.get_filter_value("company");

				return {
					filters: {
						company: company,
						is_group: 0
					}
				};
			},
			description: __("Optional. Select only if consultant payment is posted through Journal Entry.")
		},
		{
			fieldname: "include_others",
			label: __("Include Others"),
			fieldtype: "Check",
			default: 0,
			description: __("Tick to include Musterroll/OAP/Operator/GFG/DFG from MR Payment and Consultant JE if account is selected.")
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