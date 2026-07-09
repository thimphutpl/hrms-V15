frappe.ui.form.on("Semso Entry", {
    // validate: function(frm) {
    //     if (frm.doc.posting_date < frappe.datetime.get_today()) {
    //         frappe.msgprint("Past dates are not allowed for Posting Date");
    //         frappe.validated = false;
    //     }
    // },
    refresh: function(frm) {
        frm.set_value("posting_date", frappe.datetime.get_today());
        frm.set_query("employee", "deceased", function (doc, cdt, cdn) {
            return {
                filters: {
                    company: frm.doc.company,
                    employee_group:frm.doc.employee_group
                }
            };
        });
         frm.set_query("semso_contribution", "semso_contributor", function (doc, cdt, cdn) {
            return {
                filters: {
                    company: frm.doc.company,
                }
            };
        });



        frm.set_query("branch",function(){
            if (!frm.doc.company){
                return
            }
            return{
                filters:{
                    company:frm.doc.company
                }
            }
        })
        frm.set_query("employee_group",function(){
            if (!frm.doc.company){
                return
            }
            return{
                filters:{
                    company:frm.doc.company
                }
            }
        })
    },

    company:function(frm){
        frm.set_value("branch","")
        frm.set_value("employee_group","")
        frm.set_value("deceased",[]),
        frm.set_value("semso_contribution",[])

    },
    employee_group: function(frm) {
        if (!frm.doc.employee_group == ""){
            frm.set_df_property("semso_contributor","hidden",0)
            frm.set_df_property("deceased","hidden",0)
            frm.set_df_property("semso_contribution","hidden",0)
            frm.set_df_property("get_employee","hidden",0)
            frm.set_df_property("spouse_semso","hidden",0)

        }
        if (frm.doc.employee_group) {
            frm.set_df_property("semso_contributor","hidden",0)
               frm.set_df_property("deceased","hidden",0)
                 frm.set_df_property("semso_contribution","hidden",0)
                   frm.set_df_property("get_employee","hidden",0)
                   frm.set_df_property("spouse_semso","hidden",0)
          
        } else {
            // hide both
           frm.set_df_property("semso_contributor","hidden",1)
              frm.set_df_property("deceased","hidden",1)
                frm.set_df_property("semso_contribution","hidden",1)
                  frm.set_df_property("get_employee","hidden",1)
                  frm.set_df_property("spouse_semso","hidden",1)
         
        }
    },

    get_employee: function(frm) {
        frm.clear_table("semso_contribution");
        if (!frm.doc.company) {
            frappe.msgprint(__("Please select Company first"));
            return;
        }
        
        
        frappe.call({
            method: "hrms.hr.doctype.semso_entry.semso_entry.get_employee",
            args: {
                "company": frm.doc.company,
                "semso_contributor":frm.doc.semso_contributor 
            },
            callback: function(res) {
            
                
                if (res.message && res.message.length > 0) {
                    res.message.forEach(function(row) {
                        let child = frm.add_child("semso_contribution");
                        child.employee = row.name;
                        child.name1 = row.employee_name;
                        child.grade = row.grade;
                        child.amount = row.amount;
                        child.base_amount =row.amount;
                    });
                    
                    frm.refresh_field("semso_contribution");

                } else {
                    frappe.msgprint({
                        title: __("No Employees Found"),
                        indicator: "orange",
                        message: __("No employees found. Please check one of Semso Contribution groups.")
                });
                    
                    frm.clear_table("semso_contribution");
                    frm.refresh_field("semso_contribution");
                }
            }
        });
    }
});