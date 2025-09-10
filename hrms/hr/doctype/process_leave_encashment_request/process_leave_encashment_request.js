// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt


frappe.ui.form.on('Process Leave Encashment Request', {
	setup: function(frm) {
		frm.set_query("leave_period", function() {
			return {
				filters: {
					is_active: 1
				}
			}
		});
	},
	refresh: function(frm) {
		if (((frm.doc.items || []).length) && frm.doc.docstatus == 1) {
			frm.page.add_action_item(__('Create Leave Encashment Request'), function() {
				frm.events.create_leave_encashment_request(frm);
			});
		}
		if (((frm.doc.items || []).length) && frm.doc.docstatus == 1) {
			frm.page.add_action_item(__('Submit all leave Encashment Request'), function() {
				frm.events.submit_leave_encashment_request(frm);
			});
		}
	},
	get_employees: function(frm) {
		if(frm.doc.docstatus == 0 && frm.doc.fiscal_year) {
			return frappe.call({
				method: "get_employees",
				doc: frm.doc,
				callback: function(r, rt) {
					frm.refresh_field("items");
					frm.refresh_fields();
				}
			});
		}
	},
	create_leave_encashment_request: function(frm) {
		return frappe.call({
			doc: frm.doc,
			method: "create_ler_for_employees",
			callback: function(r) {
				frm.refresh();
				// frm.toolbar.refresh();
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Creating Leave Encashment Request...</span>'
		})
	},

    submit_leave_encashment_request:function(frm) {
        frm.call({
            doc: frm.doc,
            method: "submit_leave_encashment_request",
            callback: function(r) {
                frm.refresh();
                frm.toolbar.refresh();
            },
            freeze: true,
            freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Submitting Leave Encashment Request...</span>'
        })
    },
});
