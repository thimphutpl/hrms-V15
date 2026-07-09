// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
var in_progress = false;

frappe.ui.form.on('Payroll Entry', {
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
		frm.set_query("branch", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
		frm.set_query("processing_branch", function() {
			return {
				"filters": {
					"company": frm.doc.company,
					"disabled":0
					
				}
			};
		});
		frm.set_query("designation", function() {
			return {
				"filters": {
					"company": frm.doc.company,
				}
			};
		});
	
	},

	refresh: function(frm) {
		if (frm.doc.docstatus == 0) {
			frm.set_intro("");
			if(!frm.is_new() && !frm.doc.salary_slips_created) {
				frm.page.clear_actions_menu();
				frm.page.clear_primary_action();
				if(!frm.doc.successful){
					frm.page.add_action_item(__("Get Employees"),
						function() {
							frm.events.get_employee_details(frm);
						}
					);
				}
				if ((frm.doc.employees || []).length) {
					frm.page.add_action_item(__('Create Salary Slips'), function() {
						frm.events.create_salary_slips(frm);
					});
				}
				if(frm.doc.successful){
					// Cancel salary slips
					frm.page.add_action_item(__('Cancel Salary Slips'), function() {
						frm.save('Cancel').then(()=>{
							frm.page.clear_actions_menu();
							frm.page.clear_primary_action();
							frm.refresh();
							frm.events.refresh(frm);
						});
					});
				}
			} else if(frm.doc.salary_slips_created){
				frm.page.clear_actions_menu();
				frm.page.clear_primary_action();
				if(!frm.doc.salary_slips_submitted){
					// Submit salary slips
					frm.page.add_action_item(__('Submit Salary Slips'), function() {
						frm.save('Submit').then(()=>{
							frm.page.clear_actions_menu();
							frm.page.clear_primary_action();
							frm.refresh();
							frm.events.refresh(frm);
						});
					});

					// Cancel salary slips
					frm.page.add_action_item(__('Cancel Salary Slips'), function() {
						frm.save('Cancel').then(()=>{
							frm.page.clear_actions_menu();
							frm.page.clear_primary_action();
							frm.refresh();
							frm.events.refresh(frm);
						});
					});
				}
			}
		} else if(frm.doc.docstatus == 1){
			// cur_frm.page.clear_actions();
			// if(frm.doc.salary_slips_submitted || (frm.doc.__onload && frm.doc.__onload.submitted_ss)) {
			// 	frm.events.add_bank_entry_button(frm);
			// }
			frm.events.add_bank_entry_button(frm);
		}else{
			cur_frm.page.clear_actions();
		}
		// if (frm.doc.docstatus == 1) {
		// 	if (frm.custom_buttons) frm.clear_custom_buttons();
		// 	frm.events.add_context_buttons(frm);
		// }
	},


	get_employee_details: function (frm) {
		frm.set_value("number_of_employees", 0);
		frm.refresh_field("number_of_employees");
		return frappe.call({
			doc: frm.doc,
			method: 'fill_employee_details',
			callback: function(r) {
				if (r.message){
					frm.set_value("number_of_employees", r.message);
					frm.refresh_field("number_of_employees");
					frm.refresh_field("employees");
					frm.dirty();
					// Following code commented by SHIV on 2020/10/20
					/*
					if(r.docs[0].validate_attendance){
						render_employee_attendance(frm, r.message);
					}
					*/
				}
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Fetching Employee Records...</span>'
		});
	},

	create_salary_slips: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "create_salary_slips",
			callback: function(r) {
				frm.refresh();
				frm.toolbar.refresh();
				// frappe.show_progress('Payroll', 10, 100, 'Queued successfully');
			},
			freeze: true,
			freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Creating Salary Slips...</span>'
		})
	},

	add_context_buttons: function(frm) {
		if(frm.doc.salary_slips_submitted || (frm.doc.__onload && frm.doc.__onload.submitted_ss)) {
			frm.events.add_bank_entry_button(frm);
		} else if(frm.doc.salary_slips_created) {
			frm.add_custom_button(__("Submit Salary Slip"), function() {
				submit_salary_slip(frm);
			}).addClass("btn-primary");
		}
	},

	add_bank_entry_button: function(frm) {
		frappe.call({
			method: 'hrms.payroll.doctype.payroll_entry.payroll_entry.payroll_entry_has_bank_entries',
			args: {
				'name': frm.doc.name
			},
			callback: function(r) {
				if (r.message && !r.message.submitted) {
					//following line is replaced with subsequent by SHIV on 2020/10/21
					//frm.add_custom_button("Make Bank Entry", function() {
					frm.add_custom_button("Make Accounting Entries", function() {
						make_accounting_entry(frm);
					}).addClass("btn-primary");
				}
			}
		});
	},

	setup: function (frm) {
		frm.add_fetch('company', 'cost_center', 'cost_center');

		frm.set_query("payment_account", function () {
			var account_types = ["Bank", "Cash"];
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		}),
		frm.set_query("cost_center", function () {
			return {
				filters: {
					"is_group": 0,
					company: frm.doc.company
				}
			};
		}),
		frm.set_query("project", function () {
			return {
				filters: {
					company: frm.doc.company
				}
			};
		});
		frm.set_query("processing_branch", function() {
            return {
                filters: {
                    "company": frm.doc.company
                }
            };
        });
		// doesn't work when in Draft
		// var status = {"Draft": "tomato",
		// 		"Failed": "red",
		// 		"Success": "green",
		// 		"Cancelled": "black"
		// 		};
		// frm.set_indicator_formatter('status',
		// 	function(doc) {
		// 		return status[doc.status];
		// });
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

	// Version.2020.10.20 Begins, following code commented by SHIV on 2020/10/20
	// following code added by SHIV on 2020/10/21
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
});

// Submit salary slips

const submit_salary_slip = function (frm) {
	frappe.confirm(__('This will submit Salary Slips, you will not be able to Cancel the submitted Salary Slips. Do you want to proceed?'),
		function() {
			frappe.call({
				method: 'submit_salary_slips',
				args: {},
				callback: function() {
					frm.events.refresh(frm);
					frm.refresh();
					frm.toolbar.refresh();
				},
				doc: frm.doc,
				freeze: true,
				freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Submitting Salary Slips...</span>'
			});
		},
		function() {
			if(frappe.dom.freeze_count) {
				frappe.dom.unfreeze();
				frm.events.refresh(frm);
			}
			frm.refresh();
			frm.toolbar.refresh();
		}
	);
};

// Ver.2020.10.21 Begins, by SHIV on 2020/10/21
// following code added by SHIV on 2020/10/21
let make_accounting_entry = function (frm) {
	var doc = frm.doc;

	return frappe.call({
		doc: cur_frm.doc,
		method: "make_accounting_entry",
		callback: function() {
			// frappe.set_route(
			// 	'List', 'Journal Entry', {"Journal Entry Account.reference_name": frm.doc.name}
			// );
			frappe.set_route(
				'List', 'Journal Entry', {"reference_type": frm.doc.doctype, "reference_name": frm.doc.name}
			);
		},
		freeze: true,
		freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Creating Payment Entries...</span>'
	});
};
