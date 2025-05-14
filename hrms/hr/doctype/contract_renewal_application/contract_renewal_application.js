// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Contract Renewal Application", {
	refresh: function(frm) {

	},
    "employee": function(frm){
        frappe.call({
			method:"update_form_value",
			doc: frm.doc,
			args:{},
			callback: function(r){
                console.log("I am evoked again")
				frm.refresh_fields();

			}
		})
    }
});
