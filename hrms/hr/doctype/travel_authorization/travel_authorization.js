// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "employee_name", "employee_name")
cur_frm.add_fetch("employee", "grade", "grade")
cur_frm.add_fetch("employee", "designation", "designation")
cur_frm.add_fetch("employee", "department", "department")
cur_frm.add_fetch("employee", "division", "division")
cur_frm.add_fetch("employee", "branch", "branch")
cur_frm.add_fetch("employee", "cost_center", "cost_center")

frappe.ui.form.on('Travel Authorization', {
	refresh: function (frm) {
		if (frm.doc.docstatus == 1 && !frm.doc.travel_claim) {
			if (frm.doc.end_date_auth < frappe.datetime.get_today()) {
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
			}
		}

		cur_frm.set_df_property("items", "read_only", frm.doc.travel_claim ? 1 : 0)
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

		if(frm.doc.currency=="BTN"){
			frm.set_value("exchange_rate", 1);
		}

		frm.set_query("employee", erpnext.queries.employee);
	},

	employee: function (frm) {
		frappe.call({
			method: "set_dsa_per_day",
			doc: frm.doc,
			callback: function(r) {
				frm.set_value("dsa_per_day", r.message)
				frm.refresh_field("dsa_per_day");
			}
		});
	},
	
	need_advance: function (frm) {
		frm.toggle_reqd("estimated_amount", frm.doc.need_advance == 1);
		frm.toggle_reqd("currency", frm.doc.need_advance == 1);
		frm.toggle_reqd("advance_amount", frm.doc.need_advance == 1);
		calculate_advance(frm);
	},

	currency: function (frm) {
		calculate_advance(frm);
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

	set_dynamic_field_label: function (frm) {
		// frm.trigger("change_grid_labels");
		frm.trigger("change_form_labels");
	},

	change_form_labels: function (frm) {
		let company_currency = erpnext.get_currency(frm.doc.company);
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

frappe.ui.form.on("Travel Authorization Item", {
	form_render: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];

		// Set query for 'country' field if place_type is "In-Country"
		if (frm.doc.place_type === "In-Country") {
			console.log(frm.doc.place_type);
			frm.set_query('country', 'items', function () {
				return {
					filters: {
						name: ['in', ['Bhutan']]
					}
				};
			});
		}

		// Get docfields for dynamic control
		let halt = frappe.meta.get_docfield("Travel Authorization Item", "halt", cur_frm.doc.name);
		// let halt_at = frappe.meta.get_docfield("Travel Authorization Item", "halt_at", cur_frm.doc.name);
		let return_same_day = frappe.meta.get_docfield("Travel Authorization Item", "return_same_day", cur_frm.doc.name);

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
				// frappe.model.set_value(cdt, cdn, "to_date", null);
			}
		}

		if (item.to_date >= item.from_date) {
			// frappe.throw("here"+String(1 + cint(frappe.datetime.get_day_diff(item.till_date, item.date))))
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
			console.log(item.no_days)
		}

		frm.refresh_fields();
		frm.refresh_field("items");
	},

	to_date: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		frappe.call({
			method: "check_date_overlap",
			doc: frm.doc,
		})
		if (item.to_date >= item.from_date) {
			// frappe.throw("here"+String(1 + cint(frappe.datetime.get_day_diff(item.till_date, item.date))))
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
			console.log(item.no_days)
		}
		else {
			if (item.to_date) {
				msgprint("To Date cannot be earlier than From Date")
				frappe.model.set_value(cdt, cdn, "to_date", "")
			}
		}
		
		frm.refresh_fields();
		frm.refresh_field("items");
	},

	exchange_rate: function (frm, cdt, cdn) {
		frm.refresh_field("items");
		frm.refresh_fields();
	},

	halt: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		cur_frm.toggle_reqd("to_date", item.halt);
		if (!item.halt) {
			frappe.model.set_value(cdt, cdn, "no_days", 1)
		} else {
			frappe.model.set_value(cdt, cdn, "travel_from", "");
			frappe.model.set_value(cdt, cdn, "travel_to", "");
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
		}
	},
});

function calculate_advance(frm) {
	frappe.call({
		method: "set_estimate_amount",
		doc: frm.doc,
		callback: function(r) {
			frm.set_value("estimated_amount", r.message)
			frm.refresh_field("estimated_amount");
		}
	});
}