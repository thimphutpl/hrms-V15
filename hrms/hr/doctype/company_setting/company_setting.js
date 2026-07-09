// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Company Setting", {
	// refresh(frm) {

	// },
   setup:function(frm){
        const filterByCompany=()=>{
            return{
                filters:{
                    "company":frm.doc.company
                }
            }
        };
        frm.set_query("tax_on_salary",filterByCompany);
        frm.set_query("tax_deducted",filterByCompany);
        frm.set_query("house_rent",filterByCompany);
        frm.set_query("health_contribution",filterByCompany);
        frm.set_query("sale_proceed",filterByCompany);
        frm.set_query("interest_on_loan",filterByCompany);
        frm.set_query("departmental_and_supervision_charge",filterByCompany);
        frm.set_query("other_revenue",filterByCompany);
 
    },
});
