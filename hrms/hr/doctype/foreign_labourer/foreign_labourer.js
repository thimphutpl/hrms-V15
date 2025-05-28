// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Foreign Labourer', {
	setup: function(frm){
                frm.get_field('internal_work_history').grid.editable_fields = [
                        {fieldname: 'branch', columns: 3},
                        {fieldname: 'cost_center', columns: 3},
                        {fieldname: 'from_date', columns: 3},
                        {fieldname: 'to_date', columns: 3},
                ];

		frm.get_field('status_details').grid.editable_fields = [
                        {fieldname: 'status', columns: 3},
                        {fieldname: 'from_date', columns: 3},
                        {fieldname: 'to_date', columns: 3},
                ];
        },
	
	refresh: function(frm) {
		// Always toggle required for date_of_separation based on status
		cur_frm.toggle_reqd("date_of_separation", frm.doc.status == "Left");

		// Add Unfreeze Operator button if status is Left
		if (frm.doc.status === "Left") {
			frm.add_custom_button(__("Unfreeze Labourer"), () => {
				frappe.call({
					method: "hrms.hr.doctype.foreign_labourer.foreign_labourer.rejoin_foreign_labourer",
					args: { docname: frm.doc.name },
					callback: () => {
						window.location.reload();
					}
				});
			});
		}
	},

	onload: function(frm) {
		if(!frm.doc.date_of_joining) {
			cur_frm.set_value("date_of_joining", get_today())
		}	
	},

	"status": function(frm) {
		cur_frm.toggle_reqd("date_of_separation", frm.doc.status == "Left")
	},
	branch: function(frm) {
		frm.__cost_center_autofetch = true;
	},
	cost_center: function(frm){
		if (frm.__cost_center_autofetch) {			
			frm.__cost_center_autofetch = false;
			return;
		}
		if (!frm.__cost_center_checked) {
			frm.__cost_center_checked = true;
			if(!frm.doc.__islocal){
				cur_frm.set_value("date_of_transfer",frappe.datetime.nowdate());
				refresh_many(["date_of_transfer"]);
				validate_prev_doc(frm,__("Please select date of transfer to new cost center"));		
			}			
			setTimeout(() => { frm.__cost_center_checked = false; }, 1000);
		}
	},
});

frappe.ui.form.on("Foreign Labourer", "refresh", function(frm) {
    cur_frm.set_query("cost_center", function() {
        return {
            "filters": {
		"is_group": 0,
		"is_disabled": 0
            }
        };
    });
})

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
