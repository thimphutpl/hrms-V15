// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Muster Roll Monthly Attendance Sheet"] = {
	"filters": [
		{
			"fieldname":"month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": "Jan\nFeb\nMar\nApr\nMay\nJun\nJul\nAug\nSep\nOct\nNov\nDec",
			"default": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
				"Dec"][frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth()],
		},
		{
			"fieldname": "year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd": 1
	    },
		{
			"fieldname":"employee_type",
			"label": __("Employee Type"),
			"fieldtype": "Select",
			"options": ['Muster Roll Employee'],
			"reqd": 1
		},
		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"reqd": 1,
			"get_query": function() {
				return {
					'filters': [
						['Cost Center', 'disabled', '!=', '1'],
						['Cost Center', 'is_group', '!=', '1']
					]
				};
			}
		}
	],

	"onload": function (me) {
			return frappe.call({
					method: "hrms.hr.report.muster_roll_monthly_attendance_sheet.muster_roll_monthly_attendance_sheet.get_years",
					callback: function (r) {
							var year_filter = me.filters_by_name.year;
							year_filter.df.options = r.message;
							year_filter.df.default = r.message.split("\n")[0];
							year_filter.refresh();
							year_filter.set_input(year_filter.df.default);
					}
			});
	}
}