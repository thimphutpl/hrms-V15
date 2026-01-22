// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Advance", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			return {
				filters: {
					status: "Active",
				},
			};
		});

		frm.set_query("advance_account", function () {
			if (!frm.doc.employee) {
				frappe.msgprint(__("Please select employee first"));
			}
			let company_currency = erpnext.get_currency(frm.doc.company);
			let currencies = [company_currency];
			if (frm.doc.currency && frm.doc.currency != company_currency) {
				currencies.push(frm.doc.currency);
			}

			return {
				filters: {
					root_type: "Asset",
					is_group: 0,
					company: frm.doc.company,
					account_currency: ["in", currencies],
				},
			};
		});

		frm.set_query("salary_component", function () {
			return {
				filters: {
					type: "Deduction",
				},
			};
		});
	},

	refresh(frm) {
		refresh_html(frm);
	},

	make_deduction_via_additional_salary: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.create_return_through_additional_salary",
			args: {
				doc: frm.doc,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_payment_entry: function (frm) {
		let method = "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee";
		if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "hrms.hr.doctype.employee_advance.employee_advance.make_bank_entry";
		}
		return frappe.call({
			method: method,
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_expense_claim: function (frm) {
		return frappe.call({
			method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim",
			args: {
				employee_name: frm.doc.employee,
				company: frm.doc.company,
				employee_advance_name: frm.doc.name,
				posting_date: frm.doc.posting_date,
				paid_amount: frm.doc.paid_amount,
				claimed_amount: frm.doc.claimed_amount,
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_return_entry: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.make_return_entry",
			args: {
				employee: frm.doc.employee,
				company: frm.doc.company,
				employee_advance_name: frm.doc.name,
				return_amount: flt(frm.doc.paid_amount - frm.doc.claimed_amount),
				advance_account: frm.doc.advance_account,
				mode_of_payment: frm.doc.mode_of_payment,
				currency: frm.doc.currency,
				exchange_rate: frm.doc.exchange_rate,
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	employee: function (frm) {
		frappe.db.get_value("Company", frm.doc.company, "default_employee_advance_account", (r)=>{
			if(r.default_employee_advance_account){
				frm.set_value("advance_account", r.default_employee_advance_account);
				frm.refresh_field("advance_account");
			}
		})
		if (frm.doc.employee) frm.trigger("get_employee_currency");
		if (frm.doc.employee) {
			frappe.call({
				method: "validate_employment_status",
				doc: frm.doc
			})
			frappe.run_serially([
				// () => frm.trigger('get_pending_amount'),
				() => frm.trigger('set_pay_details'),
				() => frm.trigger('set_start_end_dates'),
				() => frm.trigger('set_monthly_deduction_amount'),
				//() => frm.trigger('get_accumulated_advance_amount_from_employee_advance')
			]);
		}
	},

	posting_date: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger('set_monthly_deduction_amount'),
			]);
		}
	},

	no_of_installments: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger('set_monthly_deduction_amount'),
			]);
		}
	},

	advance_amount: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger('set_monthly_deduction_amount'),
			]);
		}
	},

	set_start_date: function (frm) {		
		frappe.call({
			method: "get_start_date",
			doc: frm.doc,
			callback: function (r) {
				if (r.message) {
					in_progress = true;
					frm.set_value("recovery_start_date", r.message.start_date);
				}
			},
		});
	},

	set_start_end_dates: function (frm) {		
		frappe.call({
			method: "get_start_end_dates",
			doc: frm.doc,
			callback: function (r) {
				if (r.message) {
					in_progress = true;
					frm.set_value("recovery_start_date", r.message.start_date);
					frm.set_value("recovery_end_date", r.message.end_date);
				}
			},
		});
	},

	set_monthly_deduction_amount: function (frm) {		
		frappe.call({
			method: "calculate_amount",
			doc: frm.doc,
			args:{'validate': 1},
			callback: function (r) {
				if (r.message) {
					in_progress = true;
					frm.set_value("deduction_amount", r.message);
				}
			},
		});
	},

	get_pending_amount: function(frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.get_pending_amount",
			args: {
				"employee": frm.doc.employee,
				"posting_date": frm.doc.posting_date
			},
			callback: function(r) {
				frm.set_value("pending_amount", r.message);
			}
		});
	},

	set_pay_details: function(frm){
		frappe.call({
			method: "set_pay_details",
			doc: frm.doc,
			args: {"update": 1},
			callback: function(r) {
				frm.refresh_field("net_pay");
				frm.refresh_field("gross_pay");
				frm.refresh_field("basic_pay");
				frm.refresh_field("advance_amount");	
			}
		})
	},

	set_default_no_of_installments: function(frm){
		frappe.call({
			method: "set_default_no_of_installments",
			doc: frm.doc,
			callback: function(r) {
				frm.refresh_field("no_of_installments");
			}
		})
	},

	get_employee_currency: function (frm) {
		frappe.db.get_value(
			"Salary Structure",
			{ employee: frm.doc.employee},
			"currency",
			(r) => {
				if (r.currency) frm.set_value("currency", r.currency);
				else frm.set_value("currency", erpnext.get_currency(frm.doc.company));
				frm.refresh_fields();
			},
		);
	},

	currency: function (frm) {
		if (frm.doc.currency) {
			var from_currency = frm.doc.currency;
			var company_currency;
			if (!frm.doc.company) {
				company_currency = erpnext.get_currency(frappe.defaults.get_default("Company"));
			} else {
				company_currency = erpnext.get_currency(frm.doc.company);
			}
			if (from_currency != company_currency) {
				frm.events.set_exchange_rate(frm, from_currency, company_currency);
			} else {
				frm.set_value("exchange_rate", 1.0);
				frm.set_df_property("exchange_rate", "hidden", 1);
				frm.set_df_property("exchange_rate", "description", "");
			}
			frm.refresh_fields();
		}
	},

	set_exchange_rate: function (frm, from_currency, company_currency) {
		frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				from_currency: from_currency,
				to_currency: company_currency,
			},
			callback: function (r) {
				frm.set_value("exchange_rate", flt(r.message));
				frm.set_df_property("exchange_rate", "hidden", 0);
				frm.set_df_property(
					"exchange_rate",
					"description",
					"1 " + frm.doc.currency + " = [?] " + company_currency,
				);
			},
		});
	},
});

var refresh_html = function(frm){
	var journal_entry_status = "";
	if(frm.doc.journal_entry_status){
		journal_entry_status = '<div style="font-style: italic; font-size: 0.8em; ">* '+frm.doc.journal_entry_status+'</div>';
	}
	
	if(frm.doc.journal_entry){
		$(cur_frm.fields_dict.journal_entry_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Journal Entry</label><br><b>'+'<a href="/desk/Form/Journal Entry/'+frm.doc.journal_entry+'">'+frm.doc.journal_entry+"</a> "+"</b>"+journal_entry_status);
	}	
}

/**
frappe.ui.form.on("Employee Advance", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			return {
				filters: {
					status: "Active",
				},
			};
		});

		frm.set_query("advance_account", function () {
			if (!frm.doc.employee) {
				frappe.msgprint(__("Please select employee first"));
			}
			let company_currency = erpnext.get_currency(frm.doc.company);
			let currencies = [company_currency];
			if (frm.doc.currency && frm.doc.currency != company_currency) {
				currencies.push(frm.doc.currency);
			}

			return {
				filters: {
					root_type: "Asset",
					is_group: 0,
					company: frm.doc.company,
					account_currency: ["in", currencies],
				},
			};
		});

		frm.set_query("salary_component", function () {
			return {
				filters: {
					type: "Deduction",
				},
			};
		});
	},

	refresh: function (frm) {
		if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.paid_amount) < flt(frm.doc.advance_amount) &&
			frappe.model.can_create("Payment Entry")
		) {
			frm.add_custom_button(
				__("Payment"),
				function () {
					frm.events.make_payment_entry(frm);
				},
				__("Create"),
			);
		} else if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount) &&
			frappe.model.can_create("Expense Claim")
		) {
			frm.add_custom_button(
				__("Expense Claim"),
				function () {
					frm.events.make_expense_claim(frm);
				},
				__("Create"),
			);
		}

		if (
			frm.doc.docstatus === 1 &&
			flt(frm.doc.claimed_amount) < flt(frm.doc.paid_amount) - flt(frm.doc.return_amount)
		) {
			if (
				frm.doc.repay_unclaimed_amount_from_salary == 0 &&
				frappe.model.can_create("Journal Entry")
			) {
				frm.add_custom_button(
					__("Return"),
					function () {
						frm.trigger("make_return_entry");
					},
					__("Create"),
				);
			} else if (
				frm.doc.repay_unclaimed_amount_from_salary == 1 &&
				frappe.model.can_create("Additional Salary")
			) {
				frm.add_custom_button(
					__("Deduction from Salary"),
					function () {
						frm.events.make_deduction_via_additional_salary(frm);
					},
					__("Create"),
				);
			}
		}
	},

	make_deduction_via_additional_salary: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.create_return_through_additional_salary",
			args: {
				doc: frm.doc,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_payment_entry: function (frm) {
		let method = "hrms.overrides.employee_payment_entry.get_payment_entry_for_employee";
		if (frm.doc.__onload && frm.doc.__onload.make_payment_via_journal_entry) {
			method = "hrms.hr.doctype.employee_advance.employee_advance.make_bank_entry";
		}
		return frappe.call({
			method: method,
			args: {
				dt: frm.doc.doctype,
				dn: frm.doc.name,
			},
			callback: function (r) {
				var doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_expense_claim: function (frm) {
		return frappe.call({
			method: "hrms.hr.doctype.expense_claim.expense_claim.get_expense_claim",
			args: {
				employee_name: frm.doc.employee,
				company: frm.doc.company,
				employee_advance_name: frm.doc.name,
				posting_date: frm.doc.posting_date,
				paid_amount: frm.doc.paid_amount,
				claimed_amount: frm.doc.claimed_amount,
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	make_return_entry: function (frm) {
		frappe.call({
			method: "hrms.hr.doctype.employee_advance.employee_advance.make_return_entry",
			args: {
				employee: frm.doc.employee,
				company: frm.doc.company,
				employee_advance_name: frm.doc.name,
				return_amount: flt(frm.doc.paid_amount - frm.doc.claimed_amount),
				advance_account: frm.doc.advance_account,
				mode_of_payment: frm.doc.mode_of_payment,
				currency: frm.doc.currency,
				exchange_rate: frm.doc.exchange_rate,
			},
			callback: function (r) {
				const doclist = frappe.model.sync(r.message);
				frappe.set_route("Form", doclist[0].doctype, doclist[0].name);
			},
		});
	},

	employee: function (frm) {
		if (frm.doc.employee) frm.trigger("get_employee_currency");
	},

	get_employee_currency: function (frm) {
		frappe.db.get_value(
			"Salary Structure",
			{ employee: frm.doc.employee},
			"currency",
			(r) => {
				if (r.currency) frm.set_value("currency", r.currency);
				else frm.set_value("currency", erpnext.get_currency(frm.doc.company));
				frm.refresh_fields();
			},
		);
	},

	currency: function (frm) {
		if (frm.doc.currency) {
			var from_currency = frm.doc.currency;
			var company_currency;
			if (!frm.doc.company) {
				company_currency = erpnext.get_currency(frappe.defaults.get_default("Company"));
			} else {
				company_currency = erpnext.get_currency(frm.doc.company);
			}
			if (from_currency != company_currency) {
				frm.events.set_exchange_rate(frm, from_currency, company_currency);
			} else {
				frm.set_value("exchange_rate", 1.0);
				frm.set_df_property("exchange_rate", "hidden", 1);
				frm.set_df_property("exchange_rate", "description", "");
			}
			frm.refresh_fields();
		}
	},

	set_exchange_rate: function (frm, from_currency, company_currency) {
		frappe.call({
			method: "erpnext.setup.utils.get_exchange_rate",
			args: {
				from_currency: from_currency,
				to_currency: company_currency,
			},
			callback: function (r) {
				frm.set_value("exchange_rate", flt(r.message));
				frm.set_df_property("exchange_rate", "hidden", 0);
				frm.set_df_property(
					"exchange_rate",
					"description",
					"1 " + frm.doc.currency + " = [?] " + company_currency,
				);
			},
		});
	},
});
*/