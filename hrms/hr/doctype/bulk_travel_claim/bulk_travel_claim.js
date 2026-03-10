// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "employee_name", "employee_name")
cur_frm.add_fetch("employee", "grade", "grade")
cur_frm.add_fetch("employee", "designation", "designation")
cur_frm.add_fetch("employee", "department", "department")
cur_frm.add_fetch("employee", "division", "division")
cur_frm.add_fetch("employee", "branch", "branch")
cur_frm.add_fetch("employee", "cost_center", "cost_center")

frappe.ui.form.on("Bulk Travel Claim", {
	setup: function(frm) {
        // Set query for employee field
        frm.set_query("employee", function() {
            return erpnext.queries.employee();
        });
        
        // Set query for approver field
        frm.set_query("approver", function() {
            if (!frm.doc.employee) {
                frappe.msgprint(__("Please select an employee first"));
                return;
            }
            
            return {
                // Correct module path - point to current doctype's method
                query: "hrms.hr.doctype.travel_authorization.travel_authorization.get_approvers",
                filters: {
                    employee: frm.doc.employee
                }
            };
        });
    },
	
	get_employee: function(frm) {
		if(frm.doc.docstatus == 0) {
			return frappe.call({
				method: "get_employee",
				doc: frm.doc,
				args: {
					branch: frm.doc.branch  // Pass the branch from the form
				},
				callback: function(r, rt) {
					// Refresh fields after update
					frm.refresh_field("employee_table");
					frm.refresh_fields();
					
					// Optional: Show message if DSA rates were found
					const employees_with_dsa = r.message.filter(e => e.dsa_per_day > 0).length;
					if (employees_with_dsa > 0) {
						frappe.show_alert({
							message: __("{0} employees with DSA rates loaded", [employees_with_dsa]),
							indicator: 'green'
						}, 3);
					}
				}
			});
		}
	},

    
    employee: function(frm) {
        // Clear approver when employee changes
        frm.set_value("approver", null);
        frm.set_value("approver_name", null);
        frm.set_value("approver_designation", null);
        // Fetch new approver if employee is selected
		frappe.call({
			method: "set_employee_supervisor",
			doc: frm.doc,
			callback: function(r){
				if(r.message){
					frm.set_value("approver", r.message[0]);
					frm.set_value("approver_name", r.message[1]);
					frm.set_value("approver_designation", r.message[2]);
					frm.refresh_fields();
				}
			}
		})
        
        // Your existing DSA calculation
        frappe.call({
            method: "set_dsa_per_day",
            doc: frm.doc,
            callback: function(r) {
                if (r.message) {
                    frm.set_value("dsa_per_day", r.message);
                    frm.refresh_field("dsa_per_day");
                }
            }
        });
    },

	refresh: function (frm) {
		// Add a button to calculate amounts
        frm.add_custom_button(__('Calculate Amounts'), function() {
            calculate_amounts(frm);
        });

		// Update total whenever amounts change
        frm.fields_dict['employee_table'].grid.wrapper.on('change', function() {
            update_total_amount(frm);
        });

		if (frm.doc.docstatus == 1 && !frm.doc.travel_claim) {
			// if (frm.doc.end_date_auth < frappe.datetime.get_today()) {
				if (!frm.doc.travel_claim) {
					frm.add_custom_button(__("Travel Claim"), function () {
						frm.trigger("create_travel_claim");
						},
						__("Create")
					);
				}
				if (!frm.doc.travel_adjustment) {
					frm.add_custom_button(__("Travel Adjustment"), function () {
						frm.trigger("create_travel_adjustment");
						}, __("Create")
					);
				}
			// }
		}

		cur_frm.set_df_property("items", "read_only", frm.doc.travel_claim ? 1 : 0)
	},

	// Optional: Auto-calculate when fields change
    employee_table_add: function(frm, cdt, cdn) {
        calculate_amounts(frm);
    },
    items_add: function(frm, cdt, cdn) {
        calculate_amounts(frm);
    },

	create_travel_adjustment: function (frm) {
		frappe.model.open_mapped_doc({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.make_travel_adjustment",
			frm: cur_frm
		})
	},

	create_travel_claim: function (frm) {
		frappe.model.open_mapped_doc({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.make_travel_claim",
			frm: cur_frm
		})
	},
	
	onload: function (frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}

		frm.set_query("employee", erpnext.queries.employee);
	},
	
	need_advance: function (frm) {
		// frm.toggle_reqd("estimated_amount", frm.doc.need_advance == 1);
		calculate_advance(frm);
		frm.toggle_reqd("advance_amount", frm.doc.need_advance == 1);
	},

	currency: function (frm) {
		// calculate_advance(frm);
		let company_currency = erpnext.get_currency(frm.doc.company);
		if (company_currency != frm.doc.company) {
			frappe.call({
				method: "erpnext.setup.utils.get_exchange_rate",
				args: {
					from_currency: company_currency,
					to_currency: frm.doc.currency,
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("exchange_rate", flt(r.message));
						frm.set_df_property(
							"exchange_rate",
							"description",
							"1 " + frm.doc.currency + " = [?] " + company_currency
						);
					}
				},
			});
		} else {
			frm.set_value("exchange_rate", 1.0);
			frm.set_df_property("exchange_rate", "hidden", 1);
			frm.set_df_property("exchange_rate", "description", "");
		}

		frm.trigger("advance_amount");
		frm.trigger("set_dynamic_field_label");
	},

	advance_amount: (frm) => {
        frm.set_value("base_advance_amount", flt(frm.doc.advance_amount) * flt(frm.doc.exchange_rate));
    },

	exchange_rate: (frm) => {
        frm.set_value("base_advance_amount", flt(frm.doc.advance_amount) * flt(frm.doc.exchange_rate));
    },

	set_dynamic_field_label: function (frm) {
		frm.trigger("change_form_labels");
	},

	change_form_labels: function (frm) {
		let company_currency = erpnext.get_currency(frm.doc.company);
		frm.set_currency_labels(["estimated_amount"], company_currency);
		frm.set_currency_labels(["base_advance_amount"], company_currency);
		frm.set_currency_labels(["advance_amount"], frm.doc.currency);

		// toggle fields
		frm.toggle_display(
			["exchange_rate", "base_advance_amount"],
			frm.doc.currency != company_currency
		);
	},
	
	make_traveil_claim: function () {
		frappe.model.open_mapped_doc({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.make_travel_claim",
			frm: cur_frm
		})
	},
});

// client‑side
function calculate_amounts(frm) {
	const items      = frm.doc.items || [];
	const employees  = frm.doc.employee_table || [];
	if (!items.length || !employees.length) return;

	const total_days = items.reduce((n, i) => n + flt(i.no_days || 0), 0);

	employees.forEach(emp => {
		const days   = flt(emp.number_of_days || total_days);
		const amount = flt(emp.dsa_per_day || 0) * days;
		frappe.model.set_value(emp.doctype, emp.name, "amount", amount);
	});

	frm.refresh_field("employee_table");
	update_total_amount(frm);
}



function update_total_amount(frm) {
    let total = 0;
    (frm.doc.employee_table || []).forEach(function(employee) {
        total += flt(employee.amount);
    });
    
    frm.set_value('total_travel_amount', total);
}

frappe.ui.form.on("Bulk Travel Claim Details", {
	onload: function(frm, cdt, cdn) {
		set_employee_dsa(frm, cdt, cdn);
		calculate_total_dsa(frm, cdt, cdn);
	},

	items_add: function(frm, cdt, cdn) {
		set_employee_dsa(frm, cdt, cdn);
		calculate_total_dsa(frm, cdt, cdn);
	},

	form_render: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		// Get docfields for dynamic control
		let halt = frappe.meta.get_docfield("Bulk Travel Claim Details", "halt", cur_frm.doc.name);
		let return_same_day = frappe.meta.get_docfield("Bulk Travel Claim Details", "return_same_day", cur_frm.doc.name);

		// Apply conditions based on item index
		if (item.idx === 1) {
			// First item: halt and halt_at are read-only; return_same_day is editable
			halt.read_only = 1;
			// halt_at.read_only = 1;
			return_same_day.read_only = 0;

			frappe.model.set_value(cdt, cdn, "halt", 0);
			// frappe.model.set_value(cdt, cdn, "halt_at", null);
		} else {
			// Other items: return_same_day is read-only; halt and halt_at are editable
			halt.read_only = 0;
			// halt_at.read_only = 0;
			return_same_day.read_only = 1;

			frappe.model.set_value(cdt, cdn, "return_same_day", 0);
		}
		frm.refresh_field("items");
	},
	
	from_date: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn];
		frappe.call({
			method: "check_date_overlap",
			doc: frm.doc,
		})
	
		if (!item.halt) {
			if (item.from_date != item.to_date || !item.to_date) {
				frappe.model.set_value(cdt, cdn, "to_date", item.to_date);
			}
		} else {
			if (item.to_date < item.from_date) {
				msgprint("To Date cannot be earlier than From Date");
			}
		}

		set_employee_dsa(frm, cdt, cdn);
		calculate_total_dsa(frm, cdt, cdn);

		frm.refresh_field("items");
		frm.refresh_fields();
	},

	to_date: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		frappe.call({
			method: "check_date_overlap",
			doc: frm.doc,
		})
		if (item.to_date >= item.from_date) {
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
		}
		else {
			if (item.to_date) {
				msgprint("To Date cannot be earlier than From Date")
				frappe.model.set_value(cdt, cdn, "to_date", "")
			}
		}
		
		set_employee_dsa(frm, cdt, cdn);
		calculate_total_dsa(frm, cdt, cdn);

		frm.refresh_field("items");
		frm.refresh_fields();
	},

	halt: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		cur_frm.toggle_reqd("to_date", item.halt);
		
		if (item.to_date && item.from_date) {
			frappe.model.set_value(cdt, cdn, "travel_from", "");
			frappe.model.set_value(cdt, cdn, "travel_to", "");
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
		}
	},

	country: function(frm, cdt, cdn) {
		set_employee_dsa(frm, cdt, cdn);
		calculate_total_dsa(frm, cdt, cdn);
	},

	exchange_rate: function (frm, cdt, cdn) {
		set_employee_dsa(frm, cdt, cdn);
		calculate_total_dsa(frm, cdt, cdn);
	},
});

const set_employee_dsa = (frm, cdt, cdn) => {
	if (frm.doc.employee) {
		let child = locals[cdt][cdn];

		if (!child.country || !frm.doc.grade) {
			return;
		}

		frappe.call({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_employee_dsa",
			args: {
				country: child.country,
				grade: frm.doc.grade,
			},
			callback: function(r) {					
				if (r.message && r.message.length > 0) {
					frappe.model.set_value(cdt, cdn, "dsa", r.message[0].dsa);
					frappe.model.set_value(cdt, cdn, "currency", r.message[0].currency);
				} else {
					frappe.model.set_value(cdt, cdn, "dsa", "");
					frappe.model.set_value(cdt, cdn, "currency", "");
				}
			},
		});
	}
};

function calculate_advance(frm) {
	frappe.call({
		method: "set_estimate_amount",
		doc: frm.doc,
		callback: function(r) {
			if (r.message) {
				frm.set_value("estimated_amount", r.message)
				frm.refresh_field("estimated_amount");
			}
		}
	});
}

function calculate_total_dsa(frm, cdt, cdn) {
    var item = locals[cdt][cdn];
	if (!item.exchange_rate) {
		item.exchange_rate = 1
	}
    if (item.dsa && item.no_days) {
		if (item.to_date && item.from_date) {
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
		} else {
			frappe.model.set_value(cdt, cdn, "no_days", 1)	
		}
		frappe.model.set_value(cdt, cdn, "dsa_nu_per_day", flt(item.dsa) * flt(item.exchange_rate))
        frappe.model.set_value(cdt, cdn, "total_dsa", flt(item.dsa_nu_per_day) * flt(item.no_days));
    }

	frm.refresh_field("items");
	frm.refresh_fields();
}
