// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Leave Travel Concession Report"] = {
	"filters": [
		{
			"fieldname": "fiscal_year",
			"label": __("Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
		},
		{
			"fieldname": "branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
		}

	],
	onload: function(report) {
        report.page.add_inner_button("Clear Filters", function () {
            report.set_filter_value("fiscal_year", null);
            report.set_filter_value("branch", null);
        });
    },
};
