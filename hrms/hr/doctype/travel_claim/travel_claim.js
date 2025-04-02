// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
// travel claim

cur_frm.add_fetch("employee", "branch", "branch");
frappe.ui.form.on('Travel Claim', {
	setup: function(frm) {
        // Set query for employee field
        frm.set_query("employee", function() {
            return erpnext.queries.employee();
        });
        
        // Set query for approver field
        frm.set_query("approver", function() {
            if (!frm.doc.employee) {
                frappe.msgprint(__("Please select an employee first"));
                return;
            }
            
            return {
                // Correct module path - point to current doctype's method
                query: "hrms.hr.doctype.travel_claim.travel_claim.get_approvers",
                filters: {
                    employee: frm.doc.employee
                }
            };
        });
    },
    
    employee: function(frm) {
        // Clear approver when employee changes
        frm.set_value("approver", null);
        frm.set_value("approver_name", null);
        frm.set_value("approver_designation", null);
        // Fetch new approver if employee is selected
		frappe.call({
			method: "get_employee_approver",
			doc: frm.doc,
			callback: function(r){
				if(r.message){
					frm.set_value("approver", r.message[0]);
					frm.set_value("approver_name", r.message[1]);
					frm.set_value("approver_designation", r.message[2]);
					frm.refresh_fields();
				}
			}
		})
    },

	onload: function (frm) {
		frm.ignore_doctypes_on_cancel_all = ['Travel Authorization', 'GL Entry', 'Payment Ledger Entry']
		let grid = frm.fields_dict['items'].grid;
        grid.cannot_add_rows = true;
	},
	
	refresh: function (frm) {
		if (frm.doc.docstatus == 1) {
			if (frappe.model.can_read("Journal Entry")) {
				cur_frm.add_custom_button('Bank Entries', function () {
					frappe.route_options = {
						"Journal Entry Account.reference_type": frm.doc.doctype,
						"Journal Entry Account.reference_name": frm.doc.name,
					};
					frappe.set_route("List", "Journal Entry");
				}, __("View"));
			}
		}
	},

	calculate_total: function (frm) {
		let total = 0,
			base_total = 0;
		frm.doc.items.forEach((item) => {
			total += item.amount;
			base_total += item.base_amount;
		});

		frm.set_value({
			total_amount: flt(total),
			base_total_amount: flt(base_total),
		});
	},

	// total_claim_amount: function (frm) {
	// 	frm.set_value("balance_amount", frm.doc.total_claim_amount + frm.doc.extra_claim_amount - frm.doc.advance_amount)
	// 	frm.refresh_field("balance_amount");
	// },
	// "extra_claim_amount": function (frm) {
	// 	frm.set_value("balance_amount", frm.doc.total_claim_amount + frm.doc.extra_claim_amount - frm.doc.advance_amount)
	// 	frm.refresh_field("balance_amount");
	// },
});

frappe.ui.form.on("Travel Claim Item", { 
	calculate: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "amount", flt(row.dsa) * flt(row.no_days) * flt(row.dsa_percent)/100);
		frappe.model.set_value(cdt, cdn, "base_amount", flt(frm.doc.exchange_rate) * flt(row.amount));
		// frm.trigger("calculate_total");
		frm.trigger("set_dynamic_field_label");
	},

	dsa: function (frm, cdt, cdn) {		
		frm.trigger("calculate", cdt, cdn);
	},

	amount: function (frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},
});