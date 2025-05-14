// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Promotion Application", {
	refresh: function(frm) {

	},
	employee: function(frm){
		get_emp_details(frm);
	}
	
});

frappe.ui.form.on('Promotion Employee Responsibilities',{
	onload:(frm,cdt,cdn)=>{
		toggle_reqd_qty_quality(frm,cdt,cdn)
	},
	form_render:(frm,cdt,cdn)=>{
		var row = locals[cdt][cdn]
		console.log(frm.fields_dict['responsibilities'].grid.grid_rows_by_docname[cdn])
		if(frappe.session.user==frm.doc.supervisor){
			frm.fields_dict['responsibilities'].grid.grid_rows_by_docname[cdn].docfields[1].read_only=1
		}else{
			frm.fields_dict['responsibilities'].grid.grid_rows_by_docname[cdn].docfields[2].read_only=1
		}
		frm.refresh_field("responsibilities")
		
	}
})

function get_emp_details(frm){
	frappe.call({
		doc: frm.doc,
		method: 'get_promotion_detail',
		callback: function(r) {
			if (r){
				frm.refresh_fields();
				frm.refresh_field("pms_rating");
				console.log("test")
			}
		}
	})
}