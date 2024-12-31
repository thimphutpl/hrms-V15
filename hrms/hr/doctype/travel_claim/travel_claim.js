// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "branch", "branch");
frappe.ui.form.on('Travel Claim', {
	
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

	// total_claim_amount: function (frm) {
	// 	frm.set_value("balance_amount", frm.doc.total_claim_amount + frm.doc.extra_claim_amount - frm.doc.advance_amount)
	// 	frm.refresh_field("balance_amount");
	// },
	// "extra_claim_amount": function (frm) {
	// 	frm.set_value("balance_amount", frm.doc.total_claim_amount + frm.doc.extra_claim_amount - frm.doc.advance_amount)
	// 	frm.refresh_field("balance_amount");
	// },
});

frappe.ui.form.on("Travel Claim Item", { 
	calculate: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "amount", flt(row.dsa) * flt(row.no_days) * flt(row.dsa_percent)/100);
		frappe.model.set_value(cdt, cdn, "base_amount", flt(frm.doc.exchange_rate) * flt(row.amount));
		// frm.trigger("calculate_total");
		frm.trigger("set_dynamic_field_label");
	},

	dsa: function (frm, cdt, cdn) {		
		frm.trigger("calculate", cdt, cdn);
	},

	amount: function (frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},
});

// frappe.ui.form.on("Travel Claim Item", {
// 	form_render: function (frm, cdt, cdn) {
		
// 		frappe.model.set_value(cdt, cdn, "travel_authorization", frm.doc.ta);
// 		frappe.model.set_value(cdt, cdn, "currency_exchange_date", frm.doc.ta_date);
// 		frm.refresh_field("items");
// 		var item = frappe.get_doc(cdt, cdn)
		
// 		if (item.idx!=0){
// 			// console.log(frm.fields_dict['items'].grid.grid_rows_by_docname[cdn]);
// 			frm.fields_dict['items'].grid.grid_rows_by_docname[cdn].docfields[3].read_only=0
// 			frappe.model.set_value(cdt, cdn, "halt", 0)
			

// 		}
// 		if (item.halt==0){
// 			frm.fields_dict['items'].grid.grid_rows_by_docname[cdn].toggle_editable('to_place', true)
// 			frm.fields_dict['items'].grid.grid_rows_by_docname[cdn].toggle_editable('from_place', true)
// 		}
// 		frm.refresh_field("items");
// 		if (frm.doc.__islocal) {
// 			var item = frappe.get_doc(cdt, cdn)
// 			// if (item.halt == 0) {
// 			// 	var df = frappe.meta.get_docfield("Travel Claim Item", "distance", cur_frm.doc.name);
// 			// 	frappe.model.set_value(cdt, cdn, "distance", "")
// 			// 	//df.display = 0;
// 			// }

// 			// if (item.currency != "BTN") {
// 			// 	frappe.model.set_value(cdt, cdn, "amount", format_currency(flt(item.amount), item.currency))
// 			// }
// 		}
// 	},
// 	currency: function (frm, cdt, cdn) {
// 		calculate_amount(frm, cdt, cdn)
// 	},
// 	visa_fees_currency: function (frm, cdt, cdn) {
// 		calculate_amount(frm, cdt, cdn)
// 	},
// 	passport_fees_currency: function (frm, cdt, cdn) {
// 		calculate_amount(frm, cdt, cdn)
// 	},
// 	incidental_fees_currency: function (frm, cdt, cdn) {
// 		calculate_amount(frm, cdt, cdn)
// 	},
// 	dsa: function (frm, cdt, cdn) {
// 		calculate_amount(frm, cdt, cdn)
// 	},
// })

// function update_days(frm, cdt, cdn){
// 	frm.doc.items.forEach(function (d) {
// 		if(d.halt==1){
// 			const date1=new Date(d.from_date);
// 			const date2=new Date(d.to_date);
// 			let no_days=(date2-date1)/ (1000*60*60*24);
// 			no_days+=1
// 			console.log(no_days);
// 			frappe.model.set_value(cdt, cdn, "no_days", String(no_days))
// 		}
// 	})
// 	calculate_amount(frm, cdt, cdn)
// }

// function calculate_amount(frm, cdt, cdn) {
// 	//var item = frappe.get_doc(cdt, cdn)
// 	var item = locals[cdt][cdn]
// 	/*if (item.last_day) {
// 		item.dsa_percent = 0
// 	} */
// 	var amount = 0;
// 	if(frm.doc.place_type == "In-Country"){
// 		amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa) * flt(item.no_days))  + (flt(item.mileage_rate)  * flt(item.distance)) + flt(item.porter_pony_charges) + flt(item.fare_amount)) 
// 		if (item.halt == 1) {
// 			amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa)) * flt(item.no_days))+flt(item.porter_pony_charges);
// 		}
// 	}
// 	else if(frm.doc.place_type == "Out-Country"){
// 		amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa)*flt(item.no_days)) + (flt(item.mileage_rate) * flt(item.distance)) + flt(item.fare_amount)); 
// 		if (item.halt == 1) {
// 			amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa)) * flt(item.no_days));
// 		}
// 	}
// 	var mileage_amount=flt(item.mileage_rate)*flt(item.distance);
// 	frappe.model.set_value(cdt, cdn, 'mileage_amount', flt(mileage_amount));
// 	if (item.currency != "BTN") {
// 		frappe.call({
// 			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
// 			args: {
// 				"from_currency": item.currency,
// 				"to_currency": "BTN",
// 				"date": item.currency_exchange_date
// 			},
// 			async:false,
// 			callback: function (r) {
// 				if (r.message) {
// 					frappe.model.set_value(cdt, cdn, "exchange_rate", flt(r.message))
// 					frappe.model.set_value(cdt, cdn, "base_amount", flt(r.message) * flt(amount))
// 					frappe.model.set_value(cdt, cdn, "amount", flt(r.message) * flt(amount))
// 					amount = flt(r.message) * flt(amount);
// 				}
// 			}
// 		})
// 	}
// 	else {
// 		frappe.model.set_value(cdt, cdn, "base_amount", flt(amount));
// 		frappe.model.set_value(cdt, cdn, "amount", flt(amount));
// 	}
// 	//If there is visa fee
// 	if(item.visa_fees_currency != "BTN"){
// 		frappe.call({
// 			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
// 			args: {
// 				"from_currency": item.visa_fees_currency,
// 				"to_currency": "BTN",
// 				"date": item.currency_exchange_date
// 			},
// 			async: false,
// 			callback: function(vf){
// 				if(vf.message){
// 					frappe.model.set_value(cdt, cdn, "base_amount", flt(vf.message)*flt(item.visa_fees) + flt(amount))	
// 					frappe.model.set_value(cdt, cdn, "amount", flt(vf.message)*flt(item.visa_fees) + flt(amount))
// 					amount = flt(vf.message)*flt(item.visa_fees) + flt(amount);
// 				}

// 			}
// 		})
// 	}
// 	else {
// 		frappe.model.set_value(cdt, cdn, "base_amount", flt(item.visa_fees) + flt(amount))
// 		frappe.model.set_value(cdt, cdn, "amount", flt(item.visa_fees) + flt(amount))
// 		amount = flt(item.visa_fees) + flt(amount)
// 	}
// 	//If there is passport fee
// 	if(item.passport_fees_currency != "BTN"){
// 		frappe.call({
// 			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
// 			args: {
// 				"from_currency": item.passport_fees_currency,
// 				"to_currency": "BTN",
// 				"date": item.currency_exchange_date
// 			},
// 			async: false,
// 			callback: function(vf){
// 				if(vf.message){
// 					frappe.model.set_value(cdt, cdn, "base_amount", flt(vf.message)*flt(item.passport_fees) + flt(amount))	
// 					frappe.model.set_value(cdt, cdn, "amount", flt(vf.message)*flt(item.passport_fees) + flt(amount))
// 					amount = flt(vf.message)*flt(item.passport_fees) + flt(amount)
// 				}

// 			}
// 		})
// 	}
// 	else {
// 		frappe.model.set_value(cdt, cdn, "base_amount", flt(item.passport_fees) + flt(amount))
// 		frappe.model.set_value(cdt, cdn, "amount", flt(item.passport_fees) + flt(amount))
// 		amount = flt(item.passport_fees) + flt(amount);
// 	}
// 	//If there is incidental expenses
// 	if(item.incidental_fees_currency != "BTN"){
// 		frappe.call({
// 			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
// 			args: {
// 				"from_currency": item.incidental_fees_currency,
// 				"to_currency": "BTN",
// 				"date": item.currency_exchange_date
// 			},
// 			async: false,
// 			callback: function(vf){
// 				if(vf.message){
// 					frappe.model.set_value(cdt, cdn, "base_amount", flt(vf.message)*flt(item.incidental_fees) + flt(amount))	
// 					frappe.model.set_value(cdt, cdn, "amount", flt(vf.message)*flt(item.incidental_fees) + flt(amount))
// 					amount = flt(vf.message)*flt(item.incidental_fees) + flt(amount);
// 				}

// 			}
// 		})
// 	}
// 	else {
// 		frappe.model.set_value(cdt, cdn, "base_amount", flt(item.incidental_fees) + flt(amount))
// 		frappe.model.set_value(cdt, cdn, "amount", flt(item.incidental_fees) + flt(amount))
// 	}
// 	refresh_field("amount");
// 	refresh_field("base_amount");
// }