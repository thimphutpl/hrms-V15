// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Muster Roll Attendance", {
    onload(frm) {
        frm.set_query("employee", function() {
            return {
                filters: {
                    'status': 'Active'
                }
            }
        });
    },

	refresh(frm) {
        if (frm.doc.__islocal && !frm.doc.attendance_date) {
			frm.set_value("attendance_date", frappe.datetime.get_today());
		}
	},
});
