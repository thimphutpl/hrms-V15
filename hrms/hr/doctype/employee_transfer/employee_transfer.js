// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

{% include 'hrms/hr/employee_property_update.js' %}

frappe.ui.form.on('Employee Transfer', {
	refresh: function(frm) {
		frm.call("has_benefit").then((r) => {
			if (!r.message.has_benefit) {
				if(cur_frm.doc.docstatus == 1){
					if(frappe.user.has_role("HR User")){
						frm.add_custom_button("Create Employee Benefit", function(){
							frappe.model.open_mapped_doc({
								method: "hrms.hr.doctype.employee_transfer.employee_transfer.make_employee_benefit",
								frm: frm
							})
						});
					}
				}

			}});

	}
});
