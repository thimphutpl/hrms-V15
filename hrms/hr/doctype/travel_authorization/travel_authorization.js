frappe.ui.form.on("Travel Authorization", {
	setup: function (frm) {
		frm.set_query("employee", function () {
			return {
				filters: {
					status: "Active",
				},
			};
		});
		frappe.call({
			method: "check_role",
			doc: frm.doc,
			callback: function(r){
				if(r.message){
					frm.toggle_enable("approver", r.message);
					frm.refresh_field("approver")
				}
			}
		})
	},
	refresh(frm) {
		frappe.call({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.has_travel_claim",
			args: {"name": frm.doc.name},
			callback: function(r){
			if (!r.message.has_travel_claim) {
				

				if (
					frm.doc.docstatus === 1 &&
					frappe.model.can_create("Travel Claim")
				) {
				
					frm.add_custom_button(
						__("Travel Claim"),
						function () {
							frm.events.make_travel_claim(frm);
						},
						__("Create"),
					);
				}

				if (
					frm.doc.docstatus === 1 &&
					frappe.model.can_create("Travel Adjustment")
				) {
					cur_frm.add_custom_button(
						__("Travel Adjustment"),
						function () {
							frm.events.make_travel_adjustment(frm);
						},
						__("Create")
					);
				}
			}
		}
	});
	},
	need_advance: function (frm) {
		frm.toggle_reqd("estimated_amount", frm.doc.need_advance == 1);
		calculate_advance(frm);
	},

	make_travel_claim: function (frm) {
		let method = "hrms.hr.doctype.travel_claim.travel_claim.get_travel_claim";
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

	make_travel_adjustment: function (frm) {
		frappe.model.open_mapped_doc({
			method: "hrms.hr.doctype.travel_adjustment.travel_adjustment.make_travel_adjustment",
			frm: cur_frm,
		});
	},

	

	employee: function (frm) {
		if (frm.doc.employee) 
		{
			frm.trigger("get_employee_currency");
			frm.trigger("set_verifier");
			frm.trigger("set_approver")

		}
		
	},

	// get_employee_currency: function (frm) {
	// 	frappe.db.get_value(
	// 		"Salary Structure",
	// 		{ employee: frm.doc.employee},
	// 		"currency",
	// 		(r) => {
	// 			if (r.currency) frm.set_value("currency", r.currency);
	// 			else frm.set_value("currency", erpnext.get_currency(frm.doc.company));
	// 			frm.refresh_fields();
	// 		},
	// 	);
	// },

	get_employee_currency: function (frm) {
		frappe.db.get_value(
			"Employee",
			frm.doc.employee,
			"company",
			(r) => {
				if (r && r.company) {
					let currency = erpnext.get_currency(r.company);
					frm.set_value("currency", currency);
				}
			}
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
	set_verifier: function (frm) {
		if (frm.doc.employee) {
			console.log("hi")
			return frappe.call({
				method: "hrms.hr.hr_custom_function.get_reports_to",
				args: {
					employee: frm.doc.employee,
				},
				callback: function (r) {
					if (r && r.message) {
						frm.set_value("verifier", r.message);
					}
				},
			});
		}
	},
	set_approver: function (frm) {
		if (frm.doc.employee) {
			console.log("hi")
			return frappe.call({
				method: "hrms.hr.hr_custom_function.get_approver",
				args: {
					employee: frm.doc.employee,
				},
				callback: function (r) {
					if (r && r.message) {
						frm.set_value("approver", r.message);
					}
				},
			});
		}
	},
});
function calculate_advance(frm) {
	if(frm.doc.travel_type == "Domestic"){
		frappe.call({
			method: "set_estimate_amount",
			doc: frm.doc,
			callback: function(r){
			frm.set_value("estimated_amount", r.message)
			frm.refresh_field("estimated_amount");
			}
		});
	}
	else{
		frappe.call({
			method: "make_travel_advance",
			doc: frm.doc,
			callback: function(r){
			frm.set_value("estimated_amount", r.message)
			frm.refresh_field("estimated_amount");
			}
		});
	}
}
frappe.ui.form.on("Travel Authorization Item", {
	from_date: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if (!child.halt && child.from_date != child.to_date) {
			if (child.from_date) {
				frappe.model.set_value(cdt, cdn, "to_date", child.from_date);
			}
		}
	},

	to_date: function(frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		if (child.from_date) {
			if (child.to_date < child.from_date) {
				msgprint("To Date cannot be earlier than From Date")
				frappe.model.set_value(cdt, cdn, "to_date", child.from_date);
			}
		}
	},
});