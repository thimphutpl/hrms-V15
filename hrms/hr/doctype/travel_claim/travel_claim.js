// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

cur_frm.add_fetch("employee", "branch", "branch");
frappe.ui.form.on('Travel Claim', {
	"items_on_form_rendered": function (frm, grid_row, cdt, cdn) {
		/*var row = cur_frm.open_grid_row();
		if(!row.grid_form.fields_dict.dsa_per_day.value) {
			row.grid_form.fields_dict.dsa.set_value(frm.doc.dsa_per_day)
                	row.grid_form.fields_dict.dsa.refresh()
		}*/
	},
	
	refresh: function (frm) {
		if (frm.doc.docstatus == 1) {
			cur_frm.set_df_property("hr_approval", "hidden", 0)
			cur_frm.set_df_property("supervisor_approval", "hidden", 0)

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
	onload: function (frm) {
		cur_frm.set_df_property("supervisor_approval", "hidden", 1)
		cur_frm.set_df_property("hr_approval", "hidden", 1)
		cur_frm.set_df_property("claim_status", "hidden", 1)

		// frm.set_query("supervisor", function () {
		// 	return {
		// 		query: "erpnext.hr.doctype.leave_application.leave_application.get_approvers",
		// 		filters: {
		// 			employee: frm.doc.employee
		// 		}
		// 	};
		// });
		/*
		if (in_list(frappe.user_roles, "Approver") && frappe.session.user == frm.doc.supervisor) {
			cur_frm.set_df_property("supervisor_approval", "hidden", 0)
			cur_frm.set_df_property("claim_status", "hidden", 0)
		}
		if (in_list(frappe.user_roles, "HR Manager") || in_list(frappe.user_roles, "HR Support"))  {
			cur_frm.set_df_property("hr_approval", "hidden", 0)
			cur_frm.set_df_property("claim_status", "hidden", 0)
		}
		*/

		if (frm.doc.docstatus == 1) {
			//cur_frm.set_df_property("hr_approval", "hidden", 0)
			//cur_frm.set_df_property("supervisor_approval", "hidden", 0)

			//if(frappe.model.can_read("Journal Entry")) {
			cur_frm.add_custom_button('Bank Entries', function () {
				frappe.route_options = {
					"Journal Entry Account.reference_type": frm.doc.doctype,
					"Journal Entry Account.reference_name": frm.doc.name,
				};
				frappe.set_route("List", "Journal Entry");
			});
			//}
		}

		if (frm.doc.docstatus < 2 || frm.doc.__islocal) {
			var ti = frm.doc.items || [];
			var total = 0.0;

			frm.doc.items.forEach(function (d) {
				total += parseFloat(d.actual_amount || 0.0)
			})

			if (parseFloat(total) != parseFloat(frm.doc.total_claim_amount)) {
				frm.set_value("total_claim_amount", parseFloat(total));
			}
		}

	},
	"total_claim_amount": function (frm) {
		frm.set_value("balance_amount", frm.doc.total_claim_amount + frm.doc.extra_claim_amount - frm.doc.advance_amount)
		frm.refresh_field("balance_amount");
	},
	"extra_claim_amount": function (frm) {
		frm.set_value("balance_amount", frm.doc.total_claim_amount + frm.doc.extra_claim_amount - frm.doc.advance_amount)
		frm.refresh_field("balance_amount");
	},
});

frappe.ui.form.on("Travel Claim Item", {
	"form_render": function (frm, cdt, cdn) {
		
		frappe.model.set_value(cdt, cdn, "travel_authorization", frm.doc.ta);
		frappe.model.set_value(cdt, cdn, "currency_exchange_date", frm.doc.ta_date);
		frm.refresh_field("items");
		var item = frappe.get_doc(cdt, cdn)
		
		if (item.idx!=0){
			// console.log(frm.fields_dict['items'].grid.grid_rows_by_docname[cdn]);
			frm.fields_dict['items'].grid.grid_rows_by_docname[cdn].docfields[3].read_only=0
			frappe.model.set_value(cdt, cdn, "halt", 0)
			

		}
		if (item.halt==0){
			frm.fields_dict['items'].grid.grid_rows_by_docname[cdn].toggle_editable('to_place', true)
			frm.fields_dict['items'].grid.grid_rows_by_docname[cdn].toggle_editable('from_place', true)
		}
		frm.refresh_field("items");
		if (frm.doc.__islocal) {
			var item = frappe.get_doc(cdt, cdn)
			// if (item.halt == 0) {
			// 	var df = frappe.meta.get_docfield("Travel Claim Item", "distance", cur_frm.doc.name);
			// 	frappe.model.set_value(cdt, cdn, "distance", "")
			// 	//df.display = 0;
			// }

			// if (item.currency != "BTN") {
			// 	frappe.model.set_value(cdt, cdn, "amount", format_currency(flt(item.amount), item.currency))
			// }
		}
	},
	"currency": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"visa_fees_currency": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"passport_fees_currency": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"incidental_fees_currency": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"dsa": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"porter_pony_charges": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"visa_fees": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"passport_fees": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"incidental_fees": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"mileage_rate": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"distance": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"dsa_percent": function (frm, cdt, cdn) {
		do_update(frm, cdt, cdn)
	},
	"actual_amount": function (frm, cdt, cdn) {
		var total = 0;
		frm.doc.items.forEach(function (d) {
			total += d.actual_amount
		})
		frm.set_value("total_claim_amount", total)
	},
	from_date: function (frm, cdt, cdn) {
		update_days(frm, cdt, cdn);
		var items = frappe.get_doc(cdt, cdn)
		if(items.halt==0){
			frappe.model.set_value(cdt, cdn, "till_date", items.date)
		}
	},
	to_date: function (frm, cdt, cdn) {
		update_days(frm, cdt, cdn);
	},
})

function update_days(frm, cdt, cdn){
	frm.doc.items.forEach(function (d) {
		if(d.halt==1){
			const date1=new Date(d.from_date);
			const date2=new Date(d.to_date);
			let no_days=(date2-date1)/ (1000*60*60*24);
			no_days+=1
			console.log(no_days);
			frappe.model.set_value(cdt, cdn, "no_days", String(no_days))


		}
	})
	do_update(frm, cdt, cdn)
}

function do_update(frm, cdt, cdn) {
	//var item = frappe.get_doc(cdt, cdn)
	var item = locals[cdt][cdn]
	/*if (item.last_day) {
		item.dsa_percent = 0
	} */
	var amount = 0;
	if(frm.doc.place_type == "In-Country"){
		amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa)*flt(item.no_days))  + (flt(item.mileage_rate)  * flt(item.distance)) + flt(item.porter_pony_charges) + flt(item.fare_amount)) 
		if (item.halt == 1) {
			amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa)) * flt(item.no_days))+flt(item.porter_pony_charges);
		}
	}
	else if(frm.doc.place_type == "Out-Country"){
		amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa)*flt(item.no_days)) + (flt(item.mileage_rate) * flt(item.distance)) + flt(item.fare_amount)); 
		if (item.halt == 1) {
			amount = flt((flt(item.dsa_percent) / 100 * flt(item.dsa)) * flt(item.no_days));
		}
	}
	var mileage_amount=flt(item.mileage_rate)*flt(item.distance);
	frappe.model.set_value(cdt, cdn, 'mileage_amount', flt(mileage_amount));
	if (item.currency != "BTN") {
		frappe.call({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
			args: {
				"from_currency": item.currency,
				"to_currency": "BTN",
				"date": item.currency_exchange_date
			},
			async:false,
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "exchange_rate", flt(r.message))
					frappe.model.set_value(cdt, cdn, "actual_amount", flt(r.message) * flt(amount))
					frappe.model.set_value(cdt, cdn, "amount", flt(r.message) * flt(amount))
					amount = flt(r.message) * flt(amount);
				}
			}
		})
	}
	else {
		frappe.model.set_value(cdt, cdn, "actual_amount", flt(amount));
		frappe.model.set_value(cdt, cdn, "amount", flt(amount));
	}
	//If there is visa fee
	if(item.visa_fees_currency != "BTN"){
		frappe.call({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
			args: {
				"from_currency": item.visa_fees_currency,
				"to_currency": "BTN",
				"date": item.currency_exchange_date
			},
			async: false,
			callback: function(vf){
				if(vf.message){
					frappe.model.set_value(cdt, cdn, "actual_amount", flt(vf.message)*flt(item.visa_fees) + flt(amount))	
					frappe.model.set_value(cdt, cdn, "amount", flt(vf.message)*flt(item.visa_fees) + flt(amount))
					amount = flt(vf.message)*flt(item.visa_fees) + flt(amount);
				}

			}
		})
	}
	else {
		frappe.model.set_value(cdt, cdn, "actual_amount", flt(item.visa_fees) + flt(amount))
		frappe.model.set_value(cdt, cdn, "amount", flt(item.visa_fees) + flt(amount))
		amount = flt(item.visa_fees) + flt(amount)
	}
	//If there is passport fee
	if(item.passport_fees_currency != "BTN"){
		frappe.call({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
			args: {
				"from_currency": item.passport_fees_currency,
				"to_currency": "BTN",
				"date": item.currency_exchange_date
			},
			async: false,
			callback: function(vf){
				if(vf.message){
					frappe.model.set_value(cdt, cdn, "actual_amount", flt(vf.message)*flt(item.passport_fees) + flt(amount))	
					frappe.model.set_value(cdt, cdn, "amount", flt(vf.message)*flt(item.passport_fees) + flt(amount))
					amount = flt(vf.message)*flt(item.passport_fees) + flt(amount)
				}

			}
		})
	}
	else {
		frappe.model.set_value(cdt, cdn, "actual_amount", flt(item.passport_fees) + flt(amount))
		frappe.model.set_value(cdt, cdn, "amount", flt(item.passport_fees) + flt(amount))
		amount = flt(item.passport_fees) + flt(amount);
	}
	//If there is incidental expenses
	if(item.incidental_fees_currency != "BTN"){
		frappe.call({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_exchange_rate",
			args: {
				"from_currency": item.incidental_fees_currency,
				"to_currency": "BTN",
				"date": item.currency_exchange_date
			},
			async: false,
			callback: function(vf){
				if(vf.message){
					frappe.model.set_value(cdt, cdn, "actual_amount", flt(vf.message)*flt(item.incidental_fees) + flt(amount))	
					frappe.model.set_value(cdt, cdn, "amount", flt(vf.message)*flt(item.incidental_fees) + flt(amount))
					amount = flt(vf.message)*flt(item.incidental_fees) + flt(amount);
				}

			}
		})
	}
	else {
		frappe.model.set_value(cdt, cdn, "actual_amount", flt(item.incidental_fees) + flt(amount))
		frappe.model.set_value(cdt, cdn, "amount", flt(item.incidental_fees) + flt(amount))
	}
	// frappe.model.set_value(cdt, cdn, "amount", format_currency(amount, item.currency))
	refresh_field("amount");
	refresh_field("actual_amount");

}

frappe.ui.form.on("Travel Claim", "after_save", function (frm, cdt, cdn) {
	if (in_list(frappe.user_roles, "Approver")) {
		if (frm.doc.workflow_state && frm.doc.workflow_state.indexOf("Rejected") >= 0) {
			frappe.prompt([
				{
					fieldtype: 'Small Text',
					reqd: true,
					fieldname: 'reason'
				}],
				function (args) {
					validated = true;
					frappe.call({
						method: 'frappe.core.doctype.communication.email.make',
						args: {
							doctype: frm.doctype,
							name: frm.docname,
							subject: format(__('Reason for {0}'), [frm.doc.workflow_state]),
							content: args.reason,
							send_mail: false,
							send_me_a_copy: false,
							communication_medium: 'Other',
							sent_or_received: 'Sent'
						},
						callback: function (res) {
							if (res && !res.exc) {
								frappe.call({
									method: 'frappe.client.set_value',
									args: {
										doctype: frm.doctype,
										name: frm.docname,
										fieldname: 'reason',
										value: frm.doc.reason ?
											[frm.doc.reason, '[' + String(frappe.session.user) + ' ' + String(frappe.datetime.nowdate()) + ']' + ' : ' + String(args.reason)].join('\n') : frm.doc.workflow_state
									},
									callback: function (res) {
										if (res && !res.exc) {
											frm.reload_doc();
										}
									}
								});
							}
						}
					});
				},
				__('Reason for ') + __(frm.doc.workflow_state),
				__('Save')
			)
		}
	}
});

// frappe.ui.form.on('Travel Claim Item',{
// 	date: function(frm, cdt, cdn){
// 		update_auth(frm, cdt, cdn)	
// 	}
// })
// function update_auth(frm, cdt, cdn){
// 	var item = locals[cdt][cdn]
// 	frappe.call({
// 		method: "erpnext.hr.doctype.travel_authorization.travel_authorization.update_date_authorization",
// 		args: {
// 			"idIdx":item.idx,
// 			"auth_date": item.date,
// 			"ta_id": item.travel_authorization
// 		}
// 	})
//  }