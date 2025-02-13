// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "branch", "branch");
frappe.ui.form.on('Travel Claim', {
	onload: function (frm) {
		let grid = frm.fields_dict['items'].grid;
        grid.cannot_add_rows = true;
	},
	
	refresh: function (frm) {
		if (frm.doc.docstatus == 1) {
			if (frappe.model.can_read("Journal Entry")) {
				cur_frm.add_custom_button('Bank Entries', function () {
					frappe.route_options = {
						"Journal Entry Account.reference_type": frm.doc.doctype,
						"Journal Entry Account.reference_name": frm.doc.name,
					};
					frappe.set_route("List", "Journal Entry");
				}, __("View"));
			}
		}
	},

	currency: (frm) => {
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

		frm.trigger("amount");
		frm.trigger("set_dynamic_field_label");
	},

	set_dynamic_field_label: function (frm) {
		frm.trigger("change_grid_labels");
		frm.trigger("change_form_labels");
	},

	change_form_labels: function (frm) {
		let company_currency = erpnext.get_currency(frm.doc.company);
		frm.set_currency_labels(["base_amount"], company_currency);
		frm.set_currency_labels(["amount"], frm.doc.currency);

		frm.toggle_display(
			["exchange_rate", "base_amount"],
			frm.doc.currency != company_currency
		);
	},

    change_grid_labels: function (frm) {
		let company_currency = erpnext.get_currency(frm.doc.company);
		frm.set_currency_labels(["base_amount"], company_currency, "items");
		frm.set_currency_labels(["amount"], frm.doc.currency, "items");

		let item_grid = frm.fields_dict.items.grid;
		$.each(["base_amount"], function (i, fname) {
			if (frappe.meta.get_docfield(item_grid.doctype, fname))
				item_grid.set_column_disp(fname, frm.doc.currency != company_currency);
		});
		frm.refresh_fields();
	},

	calculate_total: function (frm) {
		let total = 0,
			base_total = 0;
		frm.doc.items.forEach((item) => {
			total += item.amount;
			base_total += item.base_amount;
		});

		frm.set_value({
			total_amount: flt(total),
			base_total_amount: flt(base_total),
		});
	},
});
frappe.ui.form.on("Travel Claim Item", { 
    mode_of_travel: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        // Toggle the visibility of fields based on mode_of_travel
        const is_personal_car = row.mode_of_travel === "Personal Car";

        frappe.model.set_value(cdt, cdn, "distance", is_personal_car ? row.distance : 0);
        frappe.model.set_value(cdt, cdn, "mileage_rate", is_personal_car ? row.mileage_rate : 0);
      
        frm.fields_dict[row.name].grid.toggle_display("distance", is_personal_car);
        frm.fields_dict[row.name].grid.toggle_display("mileage_rate", is_personal_car);
    },

    calculate: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt, cdn, "amount", flt(row.dsa) * flt(row.no_days) * flt(row.dsa_percent) / 100);
        frappe.model.set_value(cdt, cdn, "base_amount", flt(frm.doc.exchange_rate) * flt(row.amount));
        // frm.trigger("calculate_total");
        frm.trigger("set_dynamic_field_label");
    },

    dsa: function (frm, cdt, cdn) {		
        frm.trigger("calculate", cdt, cdn);
    },
	
	 // Combined dsa_percent function
	dsa_percent: function(frm, cdt, cdn){
		var item = locals[cdt][cdn];

		if(frm.doc.place_type == "Out-Country" || frm.doc.place_type == "In-Country") {
			// Calculate amount based on place_type and dsa_percent
			frappe.model.set_value(cdt, cdn, "amount", flt(flt(item.dsa) * flt(item.no_days) * flt(item.dsa_percent) * 0.01, 2));
			frm.refresh_fields();
		}
    },	

    amount: function (frm, cdt, cdn) {
        frm.trigger("calculate", cdt, cdn);
    },
});
