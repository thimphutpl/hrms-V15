// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Semso Allocated Amount", {
	 setup:function(frm){
		const getBranchFilter = () => {
            if (!frm.doc.company) {
                alert("Company is required.")
            }
            
            return {
                filters: {
                    company: frm.doc.company,
                    disabled: 0
                }
            };
        };
	    frm.set_query("branch", getBranchFilter);

	},
   // Client-side code modification
get_semso_contributor: function(frm) {
    if (!frm.doc.company) {
        frappe.msgprint(__("Please select Company first"));
        return;
    }
    
    frappe.call({
        method: "hrms.hr.doctype.semso_allocated_amount.semso_allocated_amount.get_all_semso",
        args: {
            "company": frm.doc.company,
            "branch": frm.doc.branch,
            "fiscal_year": frm.doc.fiscal_year,
            "month": frm.doc.month
        },
        callback: function(res) {
            if (res.message && res.message.length > 0) {
                frm.clear_table("semso_contribution");
                
                res.message.forEach(function(entry) {
                    if (entry.contributions && entry.contributions.length > 0) {
                        entry.contributions.forEach(function(con) {
                            let child = frm.add_child("semso_contribution");
                            child.employee = con.employee;
                            child.name1 = con.name1;
                            child.grade = con.grade;
                            child.amount = con.amount;
                        });
                    }
                });
                
                frm.refresh_field("semso_contribution");
                frappe.msgprint(__("Successfully loaded {0} contributions", [frm.doc.semso_contribution.length]));
            } else {
                frappe.msgprint(__("No Semso Entries found"));
            }
        }
    });
}
});
