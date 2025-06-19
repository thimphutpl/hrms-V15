// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Income Tax Slab', {
	currency: function(frm) {
		frm.refresh_fields();
	},
	onload_post_render: function(frm){
		if (frm.doc.docstatus === 1){
			$(".grid-footer").attr('style','');
		}
		// $(".grid-upload").addClass('hidden');
	},
});
