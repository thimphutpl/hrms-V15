// frappe.ui.form.on("Semso Entry", {
//     refresh: function(frm) {
//         frm.set_query("employee", "deceased", function() {
//             if (!frm.doc.company || !frm.doc.branch) {
//                 return {
//                     filters: {
//                         name: ["=", ""]
//                     }
//                 };
//             }
//             return {
//                 filters: {
//                     company: frm.doc.company,
//                     branch: frm.doc.branch,
//                     status: "Active"
//                 }
//             };
//         });
        
//         // Optional: Add a refresh button
//         frm.add_custom_button(__('Load Employees'), function() {
//             frm.trigger('get_employee');
//         });
//     },
    
//     // Trigger when company changes
//     company: function(frm) {
//         if (frm.doc.company) {
//             frm.trigger('get_employee');
//         }
//     },
    
//     // Trigger when troops changes
//     troops: function(frm) {
//         if (frm.doc.company) {
//             frm.trigger('get_employee');
//         }
//     },
    
//     // Trigger when officers changes (if you have this field)
//     officers: function(frm) {
//         if (frm.doc.company) {
//             frm.trigger('get_employee');
//         }
//     },
    
//     // Main function to get employees
//     get_employee: function(frm) {
//         // Clear existing rows
//         frm.clear_table("semso_contribution");
        
//         // Make sure company exists
//         if (!frm.doc.company) {
//             frappe.msgprint(__("Please select Company first"));
//             return;
//         }
        
//         frappe.call({
//             method: "hrms.hr.doctype.semso_entry.semso_entry.get_employee",
//             args: {
//                 "company": frm.doc.company,
//                 "troops": frm.doc.troops ? 1 : 0,
//                 "officers": frm.doc.officers ? 1 : 0  // Add this if you have officers field
//             },
//             callback: function(res) {
//                 if (res.message && res.message.length > 0) {
//                     res.message.forEach(function(employee) {
//                         let child = frm.add_child("semso_contribution");
//                         child.employee = employee.name;           // Or employee.employee_grade
//                         child.name1 = employee.employee_name;     // Make sure field name is 'name1' or 'name'
//                         child.grade = employee.grade;
//                     });
                    
//                     // Refresh the child table
//                     frm.refresh_field("semso_contribution");
                    
//                     // Show success message
//                     frappe.show_alert({
//                         message: __("{0} employees loaded", [res.message.length]),
//                         indicator: "green"
//                     }, 3);
//                 } else {
//                     frappe.msgprint(__("No employees found for the selected criteria"));
//                 }
//             },
//             error: function(error) {
//                 frappe.msgprint(__("Error loading employees: ") + error);
//             }
//         });
//     }
// });

frappe.ui.form.on("Semso Entry", {
    refresh: function(frm) {
        frm.set_query("employee", "deceased", function() {
            if (!frm.doc.company || !frm.doc.branch) {
                return {
                    filters: {
                        name: ["=", ""]
                    }
                };
            }
            return {
                filters: {
                    company: frm.doc.company,
                    branch: frm.doc.branch,
                    status: "Active"
                }
            };
        });
        
    },
    
   
    
    // Main function to get employees
    get_employee: function(frm) {
        // Clear existing rows
        frm.clear_table("semso_contribution");
        
        // Make sure company exists
        if (!frm.doc.company) {
            frappe.msgprint(__("Please select Company first"));
            return;
        }
        
        frappe.call({
            method: "hrms.hr.doctype.semso_entry.semso_entry.get_employee",
            args: {
                "company": frm.doc.company,
                "troops": frm.doc.troops ? 1 : 0,
                "officers": frm.doc.officers ? 1 : 0
            },
            callback: function(res) {
                if (res.message && res.message.length > 0) {
                    let skippedDeceased = 0;
                    let addedCount = 0;
                    
                    res.message.forEach(function(employee) {
                        // Check if employee already exists in DECEASED child table
                        let isInDeceasedTable = frm.doc.deceased && frm.doc.deceased.some(function(row) {
                            return row.employee === employee.name;
                        });
                        
                        if (isInDeceasedTable) {
                            skippedDeceased++;
                            return; // Skip - employee is in deceased table
                        }
                        
                        // Add to semso_contribution child table
                        let child = frm.add_child("semso_contribution");
                        child.employee = employee.name;
                        child.name1 = employee.employee_name;
                        child.grade = employee.grade;
                        addedCount++;
                    });
                    
                    // Refresh the child table
                    frm.refresh_field("semso_contribution");
                    
                    // Show success message
                    let message = __("{0} employees loaded", [addedCount]);
                    // if (skippedDeceased > 0) {
                    //     message += __(" ({0} skipped - in deceased table)", [skippedDeceased]);
                    // }
                    
                    if (addedCount > 0) {
                        frappe.show_alert({
                            message: message,
                            indicator: "green"
                        }, 3);
                    }
                    
                    if (addedCount === 0 && skippedDeceased > 0) {
                        frappe.msgprint(__("All {0} employees are already in the Deceased table. None added to Semso Contribution.", [skippedDeceased]));
                    } else if (addedCount === 0 && res.message.length === 0) {
                        frm.refresh_field("semso_contribution");
                        frappe.msgprint(__("No employees found for the selected criteria"));
                    }
                } else {
                    frm.refresh_field("semso_contribution");
                    frappe.msgprint(__("No employees found for the selected criteria"));
                }
            },
            error: function(error) {
                frappe.msgprint(__("Error loading employees: ") + error);
            }
        });
    }
});