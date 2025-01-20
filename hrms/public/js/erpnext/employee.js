// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee", {
	refresh: function (frm) {
		frm.set_query("payroll_cost_center", function () {
			return {
				filters: {
					company: frm.doc.company,
					is_group: 0,
				},
			};
		});
	},

	// date_of_birth(frm) {
	// 	frm.call({
	// 		method: "hrms.overrides.employee_master.get_retirement_date",
	// 		args: {
	// 			date_of_birth: frm.doc.date_of_birth,
	// 			grade: frm.doc.grade,
	// 		},
	// 	}).then((r) => {
	// 		if (r && r.message) frm.set_value("date_of_retirement", r.message);
	// 	});
	// },
	date_of_birth(frm) {
        calculate_retirement_date(frm);
    },
    grade(frm) {
        calculate_retirement_date(frm);
    },
});

// Function to calculate and set the retirement date
function calculate_retirement_date(frm) {
    if (frm.doc.date_of_birth && frm.doc.grade) {
        frm.call({
            method: "hrms.overrides.employee_master.get_retirement_date",
            args: {
                date_of_birth: frm.doc.date_of_birth,
                grade: frm.doc.grade,
            },
        }).then((r) => {
            if (r && r.message) {
                frm.set_value("date_of_retirement", r.message);
            }
        });
    }
}