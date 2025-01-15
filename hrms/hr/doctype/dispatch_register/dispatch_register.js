// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Dispatch Register", {
	refresh(frm) {

	},
    setup: function(frm){
        frm.set_query("department", function() {
			return {
				filters: {
					"company": frm.doc.company,

				}
			};
		});
    },
	transaction: function(frm) {
        frappe.call({
			method: "hrms.hr.doctype.dispatch_register.dispatch_register.get_employees_by_department",
			args: {
				transaction_type: frm.doc.transaction_type,
				transaction: frm.doc.transaction
			},
			callback: function(r) {
				if (r.message) {
					frm.set_value('transaction_dispatch_number', r.message);
				} else {
					frappe.msgprint(__('No dispatch number found for the given transaction.'));
				}
			}
		});
    }
});
