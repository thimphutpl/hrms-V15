frappe.ui.form.on('SWS Membership', {
        // refresh: function(frm, cdt, cdn){
        //      frappe.call({
        //              method: "update_contribution_refresh",
        //              doc: frm.doc,
        //              callback: function(r){

        //              }
        //      })
        // },
        employee: function(frm, cdt, cdn) {
                // erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "members", "employee");
                if (frm.doc.employee && frm.doc.members && frm.doc.members.length) {
                        let doctype = frm.doc.members[0].doctype;
                        $.each(frm.doc.members || [], function(i, item) {
                                frappe.model.set_value(doctype, item.name, "employee", frm.doc.employee);
                        });
                }
                // this.set_employee_in_children(doc.members, "employee", doc.employee);
        },
        // set_employee_in_children: function(child_table, employee_field, employee) {
        //      this.autofill_employee(child_table, employee_field, employee);
        // },
        // autofill_employee : function (child_table, employee_field, employee) {

        // },
});
frappe.ui.form.on('SWS Membership Item', {
        relationship: function(frm, cdt, cdn){
                var row = locals[cdt][cdn];
                if(frm.doc.employee != null || frm.doc.employee != ""){
                        frappe.model.set_value(row.doctype, row.name, "employee" ,frm.doc.employee);
                        frm.refresh_field("members");
                        frm.refresh_field("employee");
                }
                frm.set_df_property("mc_doc","reqd", frm.doc.relationship == "Spouse");
                if(frm.doc.relationship == "Father" || frm.doc.relationship == "Father-in-law"){
                        frm.set_value("gender","Male");
                        frm.refresh_field("gender");
                }
                else if(frm.doc.relationship == "Mother" || frm.doc.relationship == "Mother-in-law" ){
                        frm.set_value("gender","Female");
                        frm.refresh_field("gender");
                }
                if(frm.doc.relationship == "Self"){
                        frappe.call({
                                method: "erpnext.hr.doctype.sws_membership.sws_membership.get_self_dob",
                                args: {"employee":frm.doc.employee},
                                callback: function(r){
                                        console.log("here")
                                }
                        })
                }

        }
});