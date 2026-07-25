// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Grade", {
    refresh: function (frm) {
        toggle_pay_scale(frm);

    },
    increment_based: function (frm) {
        toggle_pay_scale(frm);

    },
    setup: function (frm) {
        frm.set_query("default_salary_structure", function () {
            return {
                filters: {
                    docstatus: 1,
                    is_active: "Yes",
                },
            };
        });

        frm.set_query("default_leave_policy", function () {
            return {
                filters: {
                    docstatus: 1,
                },
            };
        });
    },
});
function toggle_pay_scale(frm) {
    if (frm.doc.increment_based) {
        frm.set_df_property("pay_scale_section", "hidden", 1);
    } else {
        frm.set_df_property("pay_scale_section", "hidden", 0);
    }
}