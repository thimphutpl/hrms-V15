// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Deduction Type', {
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
		frm.set_query("account", function() {
			
			return {
				filters: {
					"is_group": 0
					
				}
			};
		});
    },
	refresh: function(frm) {
		
	}
});
