// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Travel Claim Report"] = {
	"filters": [
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
		
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
		}

	],
	
	onload: function(report) {
        report.page.add_inner_button("Clear Filters", function () {
            report.set_filter_value("from_date", null);
            report.set_filter_value("to_date", null);
            report.set_filter_value("cost_center", null);
            report.set_filter_value("employee", null);
        });
    },
};
