// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Information"] = {
	filters: [

		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: "Employee"

		},
		{
			fieldname: "blood_group",
			label: __("Blood Group"),
			fieldtype: "Select",
			options: "A+\nA -\nB +\nB -\nAB +\nAB -\nO +\nO -"

		}
	],
	onload: function (report) {
		report.page.add_inner_button("Clear Filters", function () {
			report.set_filter_value("employee", null);
			report.set_filter_value("blood_group", null);
		});
	},

};
