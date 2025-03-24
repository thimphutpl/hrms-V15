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
	company:function(frm){
		// frappe.set_value('employee',frappe.session.user)
		frappe.call({
			method: "hrms.hr.doctype.dispatch_register.dispatch_register.get_date_depart",
			args: {
				company: frm.doc.company,
				date: frm.doc.date,
				user: frappe.session.user
			},
			callback: function(r) {
				console.log(r.message)
				if (r.message) {
					frm.set_value('fiscal_year', r.message['fiscal_year']);
					frm.set_value('employee', r.message['employee_id']);
				} 
				// else {
				// 	frappe.msgprint(__('No dispatch number found for the given transaction.'));
				// }
			}
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
