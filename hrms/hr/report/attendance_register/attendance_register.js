// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.query_reports["Attendance Register"] = {
// 	"filters": [

// 	]
// };

frappe.query_reports["Attendance Register"] = {
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
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Select",			
			"reqd": 1
		},
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"reqd": 1,
			"get_query": function() {return {'filters': [['Cost Center', 'disabled', '!=', '1'], ['Cost Center', 'is_group', '!=', '1']]}}
		},
		{
                        "fieldname":"employee_type",
                        "label": __("Employee Type"),
                        "fieldtype": "Select",
                        "options": ['', 'Muster Roll Employee', 'Operator', 'Open Air Prisoner', 'DFG'],
			"reqd": 1
                },
	],


	"onload": function(frm) {
        frappe.call({
            method: "hrms.hr.report.attendance_register.attendance_register.get_years",
            callback: function(r) {
                if (r.message && r.message.year) {
                    frm.set_filter("year", r.message.year); // Set options
                    frm.set_value("year", r.message.year[0]); // Set default value (optional)
                    frm.refresh();
                } else {
                    console.error("Error fetching years:", r);
                }
            },
            error: function(err) {
                console.error("Error calling get_years:", err);
            }
        });
    }
}

	// "onload": function(me) {
	// 	return  frappe.call({
	// 		method: "hrms.hr.report.attendance_register.attendance_register.get_years",
	// 		callback: function(r) {
	// 			var year_filter = me.filters_by_name.year;		
	// 			year_filter.df.option = r.message;
	// 			year_filter.df.default = r.message.split("\n")[0];
	// 			year_filter.refresh();
	// 			year_filter.set_input(year_filter.df.default);
	// 		}
	// 	});
	// }
}
