// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
//

frappe.ui.form.on("Employee Group Master", {
	setup: function(frm) {

        frm.set_query("employee_group", function() {

            if (!frm.doc.company) {
                return {
                    filters: {}
                };
            }

            return {
                filters: {
                    company: frm.doc.company
                }
            };
        });
         frm.set_query("grade","employee_grade",function() {
            return {
                filters: {
                     company: frm.doc.company
                }
            };
        })

    },
   

});
