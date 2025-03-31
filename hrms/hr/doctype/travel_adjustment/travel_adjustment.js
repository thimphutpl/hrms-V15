// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Adjustment", {
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
                query: "hrms.hr.doctype.travel_adjustment.travel_adjustment.get_approvers",
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
	
	refresh(frm) {

	},
});
