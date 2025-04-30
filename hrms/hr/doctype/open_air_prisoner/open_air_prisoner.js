// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Open Air Prisoner', {
	onload: function(frm) {
		if(!frm.doc.date_of_joining) {
			cur_frm.set_value("date_of_joining", get_today())
		}	
	},
	refresh: function (frm) {
		if (frm.doc.docstatus == 1 && frm.doc.status=="Left") {
			frm.add_custom_button(__("Unfreeze OAP"), function () {
				frm.trigger("unfreeze_oap");
				}, __("Unfreeze")
			);
		}
	},
	unfreeze_oap: function (frm) {
		unfreeze_open_air_prisoner(frm);
	},
});
function unfreeze_open_air_prisoner(frm) {
	frappe.call({
		method: "unfreeze_oap",
		doc: frm.doc,
		callback: function(r) {
			frm.set_value("status", r.message)
			frm.refresh_fields();
		}
	});
}
function validate_prev_doc(frm, title){
	return frappe.call({
		method: "erpnext.custom_utils.get_prev_doc",
				args: {doctype: frm.doctype, docname: frm.docname, col_list: "cost_center,branch"},
				callback: function(r) {
					if(frm.doc.cost_center && (frm.doc.cost_center !== r.message.cost_center)){
						var d = frappe.prompt({
							fieldtype: "Date",
							fieldname: "date_of_transfer",
							reqd: 1,
							description: __("*This information shall be recorded in employee internal work history.")},
							function(data) {
								cur_frm.set_value("date_of_transfer",data.date_of_transfer);
								refresh_many(["date_of_transfer"]);
							},
							title, 
							__("Update")
						);
					}
				}
		});
}
