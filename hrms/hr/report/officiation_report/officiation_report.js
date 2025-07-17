// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Officiation Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date"
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname":"officiate",
			"label": __("Officiating Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company"
		}

	],
	onload: function(report) {
        report.page.add_inner_button("Clear Filters", function () {
            report.set_filter_value("from_date", null);
            report.set_filter_value("to_date", null);
            report.set_filter_value("employee", null);
            report.set_filter_value("officiate", null);
            report.set_filter_value("company", null);
        });
    },
};
