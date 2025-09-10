// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gewogs', {
	refresh: function(frm) {

	}
});

cur_frm.fields_dict['dzongkhag'].get_query = function(doc, dt, dn) {
       return {
               filters:{"country_name": doc.country_name}
       }
}

cur_frm.fields_dict['gewog'].get_query = function(doc, dt, dn) {
       return {
               filters:{"dzongkhag": doc.dzongkhag}
       }
}
