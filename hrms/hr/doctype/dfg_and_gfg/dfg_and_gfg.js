// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('DFG AND GFG', {	
	refresh: function(frm) {
		cur_frm.toggle_reqd("date_of_separation", frm.doc.status == "Left");

		// Add Unfreeze Operator button if status is Left and not blacklisted
		if (frm.doc.status === "Left" && frm.doc.black_listed != 1) {
			frm.add_custom_button(__("Unfreeze DFG/GFG"), () => {
				frappe.call({
					method: "hrms.hr.doctype.dfg_and_gfg.dfg_and_gfg.rejoin_dfg_gfg",
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
frappe.ui.form.on("DFG AND GFG", "refresh", function(frm) {
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
