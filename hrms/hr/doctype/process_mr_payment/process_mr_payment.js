// cur_frm.add_fetch("project", "branch", "branch")
// cur_frm.add_fetch("project", "cost_center", "cost_center")
// cur_frm.add_fetch("cost_center", "branch", "branch")

// cur_frm.add_fetch("project", "branch", "branch")
// cur_frm.add_fetch("project", "cost_center", "cost_center")
// cur_frm.add_fetch("cost_center", "branch", "branch")

frappe.ui.form.on('Process MR Payment', {
	setup: function(frm) {
		frm.get_docfield("items").allow_bulk_edit = 1;
	},
	refresh: function(frm) {
		if (frm.doc.payment_jv && frappe.model.can_read("Journal Entry")) {
			cur_frm.add_custom_button(__('Bank Entries'), function() {
				frappe.route_options = {
					"Journal Entry Account.reference_type": me.frm.doc.doctype,
					"Journal Entry Account.reference_name": me.frm.doc.name,
				};
				frappe.set_route("List", "Journal Entry");
			}, __("View"));
		}
	},
	
	// onload: function(frm) {
	// 	if(!frm.doc.from_date) {
	// 		frm.set_value("from_date", frappe.datetime.month_start(get_today()))	
	// 	}
	// 	if(!frm.doc.to_date) {
	// 		frm.set_value("to_date", frappe.datetime.month_end(get_today()))	
	// 	}
	// 	if(!frm.doc.posting_date) {
	// 		frm.set_value("posting_date", get_today())	
	// 	}
	// },

	onload: function(frm) {
		if (!frm.doc.from_date) {
			frm.set_value("from_date", frappe.datetime.month_start(frappe.datetime.get_today()));
		}
		if (!frm.doc.to_date) {
			frm.set_value("to_date", frappe.datetime.month_end(frappe.datetime.get_today()));
		}
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}
	},
	
	project: function(frm) {
		cur_frm.set_df_property("cost_center", "read_only", frm.doc.project ? 1 : 0)
	},

	load_records: function(frm) {
		if (!frm.doc.fiscal_year) {
			frappe.msgprint({
				title: __('Mandatory Field'),
				message: __('Please select Fiscal Year before proceeding.'),
				indicator: 'red'
			});
			return;
		}
		//cur_frm.set_df_property("load_records", "disabled",  true);
		//msgprint ("Processing wages.............")
		if(frm.doc.from_date && frm.doc.cost_center && frm.doc.employee_type && frm.doc.from_date < frm.doc.to_date) {
			get_records(frm.doc.employee_type, frm.doc.fiscal_year, frm.doc.month, frm.doc.from_date, frm.doc.to_date, frm.doc.cost_center, frm.doc.branch, frm.doc.name)
		}
		else if(frm.doc.from_date && frm.doc.from_date > frm.doc.to_date) {
			msgprint("To Date should be smaller than From Date")
			frm.set_value("to_date", "")
		}
		//cur_frm.set_df_property("load_records", "disabled", true);
	},
	load_employee: function(frm) {
		//load_accounts(frm.doc.company)
		return frappe.call({
			method: "load_employee",
			doc: frm.doc,
			callback: function(r, rt) {
				frm.refresh_field("items");
				frm.refresh_fields();
			}
		});
	}
});


function get_records(employee_type, fiscal_year, month, from_date, to_date, cost_center, branch, dn) {
	cur_frm.clear_table("items");
	cur_frm.refresh_field("items");
	frappe.call({
		method: "hrms.hr.doctype.process_mr_payment.process_mr_payment.get_records",
		args: {
			"fiscal_year": fiscal_year,
			"fiscal_month": month,
			"from_date": from_date,
			"to_date": to_date,
			"cost_center": cost_center,
			"branch": branch,
			"employee_type": employee_type,
			"dn": dn
		},
		//refresh: function(frm) {
		//	console.log("ISNIDE")
	//	},
	//	freeze: 1,
	//	freeze_message: "Processing.....Please Wait",
		callback: function(r) {
			if(r.message) {
				var total_overall_amount = 0;
				var ot_amount = 0; 
				var wages_amount = 0;
				var gratuity_amount = 0;
				var gross_loading_amount=0;
				var total_loading_wages_amount=0;
				var total_loading_over_time=0;
				//cur_frm.clear_table("items");
				console.log(r.message);
				r.message.forEach(function(mr) {
					if(mr['number_of_days'] > 0 || mr['number_of_hours'] > 0) {
						var row = frappe.model.add_child(cur_frm.doc, "MR Payment Item", "items");
						//alert(mr['employee_type'])
						
						row.employee_type 	=  mr['employee_type'];
						row.employee 		= mr['employee'];
						row.person_name 	= mr['person_name'];
						row.id_card 		= mr['id_card'];
						row.fiscal_year 	= fiscal_year;
						row.month 			= month;
						row.number_of_days 	= parseFloat(mr['number_of_days']);
						row.number_of_hours = parseFloat(mr['number_of_hours']);
						row.bank = mr['bank'];
						row.account_no = mr['account_no'];
						row.designation = mr['designation'];
						row.type=mr['type']
						
						
						if(mr['type'] == 'muster roll') {
							row.daily_rate 	= mr['rate_per_day'];
							// frappe.throw(row.daily_rate)
							row.hourly_rate 	= mr['rate_per_hour'];
							
							row.gratuity_amount = 0
							row.total_ot_amount = parseFloat(mr['total_ot']);
							//row.total_wage 		= parseFloat(mr['total_wage']);
							row.total_wage = parseFloat(mr['rate_per_day'])*parseFloat(mr['number_of_days'])
						//}
							row.total_amount 	= parseFloat(row.total_ot_amount) + parseFloat(row.total_wage) - parseFloat(row.gratuity_amount);
							refresh_field("items");

							total_overall_amount += row.total_amount;
							ot_amount 			 += row.total_ot_amount;
							wages_amount 		 += row.total_wage;
							gratuity_amount     += row.gratuity_amount
						}
						if(mr['type'] == 'Unloading and loading') {
							//#alert(mr['type'])
							//msgprint("hii"+mr['type'])
							row.daily_rate 	= mr['rate_per_day'];
							// frappe.throw(row.daily_rate)
							row.hourly_rate 	= mr['rate_per_hour'];
							
							row.gratuity_amount = 0
							row.total_ot_amount = parseFloat(mr['total_ot']);
							//row.total_wage 		= parseFloat(mr['total_wage']);
							row.total_wage = parseFloat(mr['rate_per_day'])*parseFloat(mr['number_of_days'])

							row.total_amount 	= parseFloat(row.total_ot_amount) + parseFloat(row.total_wage) - parseFloat(row.gratuity_amount);
							refresh_field("items");

							gross_loading_amount += row.total_amount;
							total_loading_wages_amount 			 += row.total_wage;
							total_loading_over_time 		 += row.total_ot_amount
							gratuity_amount     += row.gratuity_amount

						}
						
						
					}
				});

				cur_frm.set_value("total_overall_amount", total_overall_amount)				
				cur_frm.set_value("wages_amount",flt(wages_amount))
				cur_frm.set_value("ot_amount", flt(ot_amount))

				cur_frm.set_value("gross_loading_amount", gross_loading_amount)				
				cur_frm.set_value("total_loading_wages_amount",flt(total_loading_wages_amount))
				cur_frm.set_value("total_loading_over_time", flt(total_loading_over_time))

				cur_frm.set_value("total_amount", flt(total_overall_amount)+flt(gross_loading_amount))

				cur_frm.set_value("gratuity_amount", flt(gratuity_amount))

				cur_frm.refresh_field("total_overall_amount")
				cur_frm.refresh_field("wages_amount")
				cur_frm.refresh_field("ot_amount")

				cur_frm.refresh_field("gross_loading_amount")
				cur_frm.refresh_field("total_loading_wages_amount")
				cur_frm.refresh_field("total_loading_over_time")

				cur_frm.refresh_field("gratuity_amount")
				cur_frm.refresh_field("total_amount")
				cur_frm.refresh_field("items");				
			}
			else {
				frappe.msgprint("No Overtime and Attendance Record Found")
			}			
		}
	})
}