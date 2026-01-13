// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["PBVA Report"] = {



	"filters": [


		{
			"fieldname": "fiscal_year",
			"label": ("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"width": "100"
		},

		{
			"fieldname": "branch",
			"label": ("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": "100"
		},


		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
		},

		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
		}


	],

	// Formatter to make totals row bold
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Bold the employee field if it's the totals row
		if (column.fieldname === "employee" && value === "<b>Total</b>") {
			value = `<strong>Total</strong>`;
		}

		// Optional: Bold numeric columns for totals row
		const total_fields = ["total_basic_pay", "tax_amount", "amount"];
		if (data && data.employee === "<b>Total</b>" && total_fields.includes(column.fieldname)) {
			value = `<strong>${value}</strong>`;
		}

		return value;
	}

};
