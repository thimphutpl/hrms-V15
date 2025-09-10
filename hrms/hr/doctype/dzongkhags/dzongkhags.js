// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Dzongkhags', {
	refresh: function(frm) {

	}
});

cur_frm.fields_dict['dzongkhag'].get_query = function(doc, dt, dn) {
       return {
               filters:{"country_name": doc.country_name}
       }
}
