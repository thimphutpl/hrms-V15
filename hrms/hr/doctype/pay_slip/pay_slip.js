// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pay Slip", {
	refresh(frm) {

	},

    employee: function (frm) {
        frm.events.get_emp_and_working_day_details(frm);
    },

    month: function (frm) {
		frm.trigger("set_start_end_dates");
	},

    get_emp_and_working_day_details: function (frm) {
		if (frm.doc.employee) {
			return frappe.call({
				method: "get_emp_and_working_day_details",
				doc: frm.doc,
				callback: function (r) {
					frm.refresh();
					// frm.trigger("update_currency_changes");
				},
			});
		}
	},

    set_start_end_dates: function (frm) {
		frappe.call({
			method: "hrms.hr.hr_custom_function.get_start_end_dates",
			args: {
				fiscal_year: frm.doc.fiscal_year,
				month: frm.doc.month,
			},
			callback: function (r) {
				if (r.message) {
					in_progress = true;
					frm.set_value("start_date", r.message.start_date);
					frm.set_value("end_date", r.message.end_date);
				}
			},
		});
	},
});
