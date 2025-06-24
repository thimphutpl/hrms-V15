// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("DSA Out Country", {
    refresh: function (frm) {},

	currency: (frm) => {
		frm.trigger("set_dynamic_field_label");
	},

	set_dynamic_field_label: function (frm) {
		frm.trigger("change_grid_labels");
	},

	change_grid_labels: function (frm) {

		frm.set_currency_labels(["dsa"], frm.doc.currency, "country_dsa_detail");
        

		frm.refresh_fields();
	},

 });
