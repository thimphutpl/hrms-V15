// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Foreign Labourer", {
// 	refresh(frm) {

// 	},
// });

// cur_frm.add_fetch("cost_center", "branch", "branch")
// cur_frm.add_fetch("project", "cost_center", "cost_center")
// cur_frm.add_fetch("project", "branch", "branch")

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
		cur_frm.toggle_reqd("date_of_separation", frm.doc.status == "Left")
	},

	onload: function(frm) {
		if(!frm.doc.date_of_joining) {
			cur_frm.set_value("date_of_joining", get_today())
		}	
	},

	"status": function(frm) {
		cur_frm.toggle_reqd("date_of_separation", frm.doc.status == "Left")
	},
	// branch: function(frm){
    //             if(frm.doc.branch){
    //                     frappe.call({
    //                             method: 'frappe.client.get_value',
    //                             args: {
    //                                     doctype: 'Cost Center',
    //                                     filters: {
    //                                             'branch': frm.doc.branch,
	// 											'is_group': 0
    //                                     },
    //                                     fieldname: ['name']
    //                             },
    //                             callback: function(r){
    //                                     if(r.message){
    //                                             cur_frm.set_value("cost_center", r.message.name);
    //                                             refresh_field('cost_center');
    //                                     }
    //                             }
    //                     });
    //             }
    //     },
	
	cost_center: function(frm){
		if(!frm.doc.__islocal){
			cur_frm.set_value("date_of_transfer",frappe.datetime.nowdate());
			refresh_many(["date_of_transfer"]);
			validate_prev_doc(frm,__("Please select date of transfer to new cost center"));		
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
