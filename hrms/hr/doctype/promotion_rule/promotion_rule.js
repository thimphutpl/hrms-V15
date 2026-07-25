// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Promotion Rule", {
    // refresh(frm) {

    // },
    setup: function (frm) {
        frm.set_query("grade", function () {
            return {
                filters: {
                    "company": frm.doc.company,
                }
            };
        });
    }
});
