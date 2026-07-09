frappe.ui.form.on("Semso Deduction Master", {
    refresh(frm) {
        // frm.set_df_property("employee_group","hidden",1)
        // frm.set_df_property("employee_grade","hidden",1)
        apply_ui_rules(frm);
    },

    employee_group(frm) {
        if (frm.doc.employee_group) {
            frm.set_value("employee_grade", null);
        }
        apply_ui_rules(frm);
    },

    employee_grade(frm) {
       if (!frm.doc.employee_grade) {
        // Unchecked → empty table
        frm.clear_table("semso_employee_grade");
        frm.refresh_field("semso_employee_grade");
        return;
    }

        frm.clear_table("semso_employee_grade");

        frm.set_value("employee_group", null);
            frappe.call({
            method: "hrms.hr.doctype.semso_deduction_master.semso_deduction_master.get_all_employee_group",
            args: {
                employee_group: frm.doc.emp_group
            },
            callback: function (res) {

                if (res.message && res.message.length > 0) {

                    res.message.forEach(function (d) {
                        let child = frm.add_child("semso_employee_grade");
                        child.employee_grade = d.grade;
                    });

                    frm.refresh_field("semso_employee_grade");
                }

                apply_ui_rules(frm);
            }
        });

    },
    emp_group:function(frm){
        if(frm.doc.emp_group){
            frm.set_df_property("employee_group","hidden",0)
            frm.set_df_property("employee_grade","hidden",0)
        }else{
            frm.set_df_property("employee_group","hidden",1)
            frm.set_df_property("employee_grade","hidden",1)

        }

    }
});

function apply_ui_rules(frm) {
    const has_group = !!frm.doc.employee_group;
    const has_grade = !!frm.doc.employee_grade;
    const has_emp_group = !!frm.doc.emp_group;
        frm.set_df_property("employee_group", "hidden", !has_emp_group);
    frm.set_df_property("employee_grade", "hidden", !has_emp_group);

    frm.set_df_property("amount", "hidden",has_group  ? 0 : 1);
    frm.set_df_property("amount", "reqd",has_grade  ? 0 : 1);
    frm.set_df_property("amount", "reqd",has_group  ? 1 : 0);

    // Optional: control visibility of filters
    frm.set_df_property("semso_employee_group", "hidden", has_group ? 0 : 1);
    frm.set_df_property("semso_employee_grade", "hidden", has_grade ? 0 : 1);

}
