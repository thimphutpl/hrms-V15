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
		
		//show the document status field and submit button
		if (in_list(frappe.user_roles, "Expense Approver") && frappe.session.user == frm.doc.supervisor) {
			frm.toggle_display("document_status", frm.doc.docstatus == 0);
			frm.toggle_reqd("document_status", frm.doc.docstatus == 0);
		}

		// Follwoing line temporarily replaced by SHIV on 2020/09/17, need to restore back
		if (frm.doc.docstatus == 1 && !frm.doc.travel_claim && frm.doc.workflow_state == "Approved") {
			frm.add_custom_button("Create Travel Claim", function () {
				if (frm.doc.end_date_auth < frappe.datetime.get_today()) {
					frappe.model.open_mapped_doc({
						method: "hrms.hr.doctype.travel_authorization.travel_authorization.make_travel_claim",
						frm: cur_frm
					})
				} else {
					frappe.msgprint(__('Claim is allowed only after travel completion date i.e., {0}', [frm.doc.end_date_auth]));
				}
			}).addClass((frm.doc.end_date_auth < frappe.datetime.get_today()) ? "btn-success" : "btn-danger");
		}

		if (frm.doc.docstatus == 1) {
			frm.toggle_display("document_status", 1);
		}

		if (frm.doc.__islocal) {
			frm.set_value("advance_journal", "");
		}
		cur_frm.set_df_property("items", "read_only", frm.doc.travel_claim ? 1 : 0)
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
	
	need_advance: function (frm) {
		frm.toggle_reqd("estimated_amount", frm.doc.need_advance == 1);
		frm.toggle_reqd("currency", frm.doc.need_advance == 1);
		frm.toggle_reqd("advance_amount", frm.doc.need_advance == 1);
		// calculate_advance(frm);
		
	},

	advance_amount: function (frm) {
		if (frm.doc.currency == "BTN") {
			frm.set_value("base_advance_amount", flt(frm.doc.advance_amount))
		}
		else {
			update_advance_amount(frm)
		}
	},
	
	document_status: function (frm) {
		if (frm.doc.document_status == "Rejected") {
			frm.toggle_reqd("purpose")
		}
	},
	
	make_traveil_claim: function () {
		frappe.model.open_mapped_doc({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.make_travel_claim",
			frm: cur_frm
		})
	},
	
	currency: function (frm) {
		if (frm.doc.currency == "BTN") {
			frm.set_value("base_advance_amount", flt(frm.doc.advance_amount))
		}
		else {
			update_advance_amount(frm)
		}
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

		// Refresh the field to reflect the changes in the child table
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
				msgprint("Till Date cannot be earlier than From Date");
				frappe.model.set_value(cdt, cdn, "to_date", null);
			}
		}

		if (item.to_date >= item.from_date) {
			// frappe.throw("here"+String(1 + cint(frappe.datetime.get_day_diff(item.till_date, item.date))))
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
			console.log(item.no_days)
		}

		/*
		if(item.till_date){
			if (item.till_date >= item.date) {
				frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.till_date, item.date)))
			}
			else{
				msgprint("Till Date cannot be earlier than From Date")
				frappe.model.set_value(cdt, cdn, "till_date", "")
			}
		} else {
			if(!item.halt) {
				frappe.model.set_value(cdt, cdn, "till_date", item.date);
			}
		}
		*/
		
		frm.refresh_fields();
		frm.refresh_field("items");
	},

	"to_date": function (frm, cdt, cdn) {
		
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
				msgprint("Till Date cannot be earlier than From Date")
				frappe.model.set_value(cdt, cdn, "to_date", "")
			}
		}
		
		frm.refresh_fields();
		frm.refresh_field("items");
	},

	exchange_rate: function (frm, cdt, cdn) {
		frm.refresh_fields();
		frm.refresh_field("items");
	},

	halt: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		cur_frm.toggle_reqd("to_date", item.halt);
		if (!item.halt) {
			//frappe.model.set_value(cdt, cdn, "no_days", 1)
			frappe.model.set_value(cdt, cdn, "temp_till_date", (item.till_date || item.date));
			frappe.model.set_value(cdt, cdn, "to_date", item.date)
			frappe.model.set_value(cdt, cdn, "travel_from", item.temp_from_place);
			frappe.model.set_value(cdt, cdn, "travel_to", item.temp_to_place);
			frappe.model.set_value(cdt, cdn, "temp_halt_at", item.halt_at);
			// frappe.model.set_value(cdt, cdn, "halt_at", "");
		} else {
			// frappe.model.set_value(cdt, cdn, "temp_from_place", item.travel_from);
			// frappe.model.set_value(cdt, cdn, "temp_to_place", item.to_place);
			frappe.model.set_value(cdt, cdn, "travel_from", "");
			frappe.model.set_value(cdt, cdn, "travel_to", "");
			// frappe.model.set_value(cdt, cdn, "halt_at", item.temp_halt_at);
			frappe.model.set_value(cdt, cdn, "till_date", item.temp_till_date || item.date);frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.till_date, item.date)))
		}
	},
});

function calculate_advance(frm) {
	frappe.call({
		method: "set_estimate_amount",
		doc: frm.doc,
		callback: function(r) {
			frm.refresh_fields();
			frm.refresh_field("estimated_amount");
			frm.refresh_field("advance_amount");
			frm.refresh_field("base_advance_amount");
		}
	});
}

function update_advance_amount(frm) {
	frappe.call({
		//method: "erpnext.setup.utils.get_exchange_rate",
		method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
		args: {
			"from_currency": frm.doc.currency,
			"to_currency": "BTN",
			"date": frm.doc.posting_date
		},
		callback: function (r) {
			if (r.message) {
				frm.set_value("base_advance_amount", flt(frm.doc.advance_amount) * flt(r.message))
				frm.set_value("advance_amount", flt(frm.doc.advance_amount))
				frm.set_value("estimated_amount", flt(frm.doc.estimated_amount))
				frm.set_value("exchange_rate", flt(r.message))
				//frm.set_value("advance_amount", format_currency(flt(frm.doc.advance_amount), frm.doc.currency))
				//frm.set_value("estimated_amount", format_currency(flt(frm.doc.estimated_amount), frm.doc.currency))
			}
		}
	})
}

frappe.form.link_formatters['Employee'] = function (value, doc) {
	return value
}
