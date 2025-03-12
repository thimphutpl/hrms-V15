// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Muster Roll Payment Register"] = {
	filters: [
		{
			fieldname: "fiscal_year",
			fieldtype: "Link",
			options: "Fiscal Year",
			label: __("Fiscal Year"),
			width: "100px",
		},
		{
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: ['','January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
			width: "100px",
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee",
			width: "100px",
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			width: "100px",
			reqd: 1,
		},
		// {
		// 	fieldname: "docstatus",
		// 	label: __("Document Status"),
		// 	fieldtype: "Select",
		// 	options: ["Draft", "Submitted", "Cancelled"],
		// 	default: "Submitted",
		// 	width: "100px",
		// },
	]
};
