// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

var in_progress = false;

frappe.ui.form.on('Promotion Entry', {
	onload: function (frm) {
		if (!frm.doc.posting_date) {
			frm.doc.posting_date = frappe.datetime.nowdate();
		}

		frm.set_query("department", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	},

	refresh: function(frm) {
		console.log("here")
		if (frm.doc.docstatus == 0) {
			if(!frm.is_new()) {
				frm.page.clear_primary_action();
				frm.add_custom_button(__("Get Employees"),
					function() {
						frm.events.get_employee_details(frm);
					}
				).toggleClass('btn-primary', !(frm.doc.employees || []).length);
			}
			if ((frm.doc.employees || []).length) {
				frm.page.set_primary_action(__('Create Employee Promotion'), () => {
					frm.save('Submit').then(()=>{
						frm.page.clear_primary_action();
						frm.refresh();
						frm.events.refresh(frm);
					});
				});
			}
		}
		if (frm.doc.docstatus == 1) {
			if (frm.custom_buttons) frm.clear_custom_buttons();
			frm.events.add_context_buttons(frm);
		}
	},

	get_employee_details: function (frm) {
		return frappe.call({
			doc: frm.doc,
			method: 'fill_employee_details',
			callback: function(r) {
				if (r.docs[0].employees){
					frappe.call({
						method: "check_increment_cycle",
						doc: frm.doc
					})
					frm.save();
					frm.refresh();
				}
			}
		})
	},

	create_employee_promotions: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "create_employee_promotions",
			callback: function(r) {
				frm.refresh();
				frm.toolbar.refresh();
			}
		})
	},

	add_context_buttons: function(frm) {
		if(frm.doc.promotions_created && !frm.doc.promotions_submitted) {
			frm.add_custom_button(__("Submit Employee Promotion"), function() {
				submit_employee_promotions(frm);
			}).addClass("btn-primary");
		}
	},

	company: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	department: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	designation: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	branch: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	fiscal_year: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	month_name: function (frm) {
		frm.events.clear_employee_table(frm);
	},

	clear_employee_table: function (frm) {
		frm.clear_table('employees');
		frm.refresh();
	},
	// Validate when new_employee_grade is changed in the child table
    new_employee_grade: function(frm, cdt, cdn) {
        var child = locals[cdt][cdn];

        // Check if the new_employee_grade is the same as the maximum_grade
        if (child.new_employee_grade === child.maximum_grade) {
            frappe.msgprint(__("The new employee grade cannot be the same as the maximum grade for employee {0}.", [child.employee]));
            frappe.model.set_value(cdt, cdn, 'new_employee_grade', ''); // Clear the field
        }
    },

    // Validate the entire form on submission
    validate: function(frm) {
        frm.doc.employees.forEach(function(employee) {
            // Check if the employee_grade is already the maximum_grade
            if (employee.employee_grade === employee.maximum_grade) {
                frappe.throw(__("Employee {0} has already reached the maximum grade. Promotion is not allowed.", [employee.employee]));
            }

            // Check if the new_employee_grade is the same as the maximum_grade
            if (employee.new_employee_grade === employee.maximum_grade) {
                frappe.throw(__("The new employee grade for {0} cannot be the same as the maximum grade.", [employee.employee]));
            }
        });
    }
});
// Submit salary slips

const submit_employee_promotions = function (frm) {
	frappe.confirm(__('This will submit Employee Promotion. Do you want to proceed?'),
		function() {
			frappe.call({
				method: 'submit_employee_promotions',
				args: {},
				callback: function() {frm.events.refresh(frm);},
				doc: frm.doc,
				freeze: true,
				freeze_message: 'Submitting Employee Promotions...'
			});
		},
		function() {
			if(frappe.dom.freeze_count) {
				frappe.dom.unfreeze();
				frm.events.refresh(frm);
			}
		}
	);
};
