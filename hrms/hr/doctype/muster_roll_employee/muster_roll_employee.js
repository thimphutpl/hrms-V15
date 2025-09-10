// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Muster Roll Employee", {
    onload: function(frm) {
        frm.set_query("bank_branch", "bank_accounts", function(doc, cdt, cdn) {
			let d = locals[cdt][cdn];
			return {
				filters: {
					'bank': d.bank
				}
			};
		});
    },

	refresh(frm) {

	},
});
