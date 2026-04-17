// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Semso Deduction Group", {
	// refresh(frm) {

	// },
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
});


