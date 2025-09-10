// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "employee_name", "employee_name")
cur_frm.add_fetch("employee", "branch", "branch")

frappe.ui.form.on('Overtime Application', {
	refresh: function(frm) {
		if (frm.doc.payment_jv && frappe.model.can_read("Journal Entry")) {
			cur_frm.add_custom_button(__('Bank Entries'), function() {
				frappe.route_options = {
					"Journal Entry Account.reference_type": me.frm.doc.doctype,
					"Journal Entry Account.reference_name": me.frm.doc.name,
				};
				frappe.set_route("List", "Journal Entry");
			}, __("View"));
		}

		if(frm.doc.workflow_state == "Draft" || frm.doc.workflow_state == "Rejected"){
			frm.set_df_property("approver", "hidden", 1);
			frm.set_df_property("approver_name", "hidden", 1);
		}
	},
	onload: function(frm) {
		if(!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today())
		}
		frm.set_query("approver", function() {
			return {
				query: "hrms.hr.doctype.leave_application.leave_application.get_approvers",
				filters: {
					employee: frm.doc.employee
				}
			};
		});
	},
	approver: function(frm) {
		if(frm.doc.approver){
			frm.set_value("approver_name", frappe.user.full_name(frm.doc.approver));
		}
	},
	employee: function(frm) {
		if (frm.doc.employee && frm.doc.overtime_based_on == "Hourly") {
			frappe.call({
				method: "erpnext.setup.doctype.employee.employee.get_overtime_rate",
				args: {
					employee: frm.doc.employee,
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("rate", r.message)
					}
				}
			})
		}	
	},
	overtime_based_on : function(frm) {
        if(frm.doc.employee && frm.doc.overtime_based_on == "Hourly") {
            frappe.call({
                    method: "erpnext.setup.doctype.employee.employee.get_overtime_rate",
                    args: {
                            employee: frm.doc.employee,
                    },
                    callback: function(r) {
                            if(r.message) {
                                    frm.set_value("rate", r.message)
                            }
                    }
            })
        }
	},
	rate: function(frm) {
		frm.set_value("total_amount", frm.doc.rate * frm.doc.total_hours)
	}
});


//Overtime Item  Details
frappe.ui.form.on("Overtime Application Item", {
	"number_of_hours": function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn);
	},
	items_remove: function(frm, cdt, cdn) {
		calculate_time(frm, cdt, cdn);
	},
})

function calculate_time(frm, cdt, cdn) {
	var total_time = 0;
	frm.doc.items.forEach(function(d) {
		if(d.number_of_hours) {
			total_time += d.number_of_hours
		}	
	})
	frm.set_value("total_hours", total_time)
	frm.set_value("total_amount", total_time * frm.doc.rate)
	cur_frm.refresh_field("total_hours")
	cur_frm.refresh_field("total_amount")
}
