// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Benefit Type", {
    setup(frm) {
        frm.set_query("account", "accounts", function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {
					"is_group": 0,
					"company": d.company
				}
			};
		});
		frm.set_query("gl_account", function() {
			
			return {
				filters: {
					"is_group": 0
					
				}
			};
		});
    },
    
	refresh(frm) {

	},
});
