frappe.ui.form.on("Travel Claim", {
    onload: function (frm) {
		let grid = frm.fields_dict['items'].grid;
        grid.cannot_add_rows = true;
	},
    
	refresh(frm) {
	// 	refresh_html(frm);
	// 	if (!(frm.doc.workflow_state == "Verified By Supervisor" || frm.doc.workflow_state == "Waiting Supervisor Approval")){
	// 		frm.fields_dict["items"].grid.update_docfield_property("dsa", "read_only", 1);
	// 		frm.fields_dict["items"].grid.update_docfield_property("dsa_percent", "read_only", 1);
	// 	}
	// 	else{
	// 		frm.fields_dict["items"].grid.update_docfield_property("dsa", "read_only", 0);
	// 		frm.fields_dict["items"].grid.update_docfield_property("dsa_percent", "read_only", 0);
	// 	}
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
	
	get_travel_authorization: function(frm) {
		// console.log("testing");
		get_travel_detail(frm);
	},
});

frappe.ui.form.on("Travel Claim Item", {
	mileage_rate: function (frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},

	distance: function (frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},

	calculate: function (frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        frappe.model.set_value(cdt, cdn, "mileage_amount", flt(row.mileage_rate) * flt(row.distance));
        frappe.model.set_value(cdt, cdn, "amount", flt(row.mileage_amount) + flt(row.amount));
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


function get_travel_detail(form) {
	if(form.doc.start_date && form.doc.end_date && form.doc.purpose_of_travel && form.doc.travel_type){
		frappe.call({
			method: "hrms.hr.doctype.travel_claim.travel_claim.get_travel_detail",
			async: false,
			args: {
				"employee": form.doc.employee,
				"start_date": form.doc.start_date,
				"end_date": form.doc.end_date,
				"travel_type": form.doc.travel_type,
				"purpose_of_travel": form.doc.purpose_of_travel
			},
			callback: function(r){
					if(r.message){
				var advance_amount = 0;
				var total_amount = 0;
				var dsa = 0;
				cur_frm.clear_table("items");
				r.message.forEach(function(dtl) {
							// console.log(dtl);
					var row = frappe.model.add_child(cur_frm.doc, "Travel Claim Item", "items");
					row.halt= dtl['halt'];
					row.travel_from= dtl['travel_from'];
					row.travel_to= dtl['travel_to'];
					row.from_date = dtl['from_date'];
					row.no_of_days = dtl['no_of_days'];
					row.days_allocated = dtl['no_of_days']
					row.to_date = dtl['to_date'];
					row.halt_at = dtl['halt_at'];
					row.travel_authorization = dtl['name'];
					row.last_day = dtl['last_day'];
					row.dsa = dtl['dsa'];
					dsa = dtl['dsa'];
					row.dsa_percent = dtl['dsa_percent'];
					row.currency = dtl['currency'];
					row.exchange_rate = dtl['exchange_rate'];
					var amount = dtl['no_of_days'] * (dtl['dsa'] * (dtl['dsa_percent']/100));
					var actual_amount = dtl['no_of_days'] * (dtl['dsa'] * (dtl['dsa_percent']/100)) * dtl['exchange_rate'];
					row.amount = amount; 
					row.actual_amount = actual_amount;
					total_amount += actual_amount;
					advance_amount += dtl['advance_amount'];
				});
				form.set_value("total_amount", total_amount);
				form.set_value("advance_amount", advance_amount);
				form.set_value("net_amount", total_amount - advance_amount);
				// form.set_value("dsa", dsa);
							cur_frm.refresh();
					}
					else {
							frappe.msgprint("No unclaimed Travel Authorization found!")
					}
				}
			});
	
	} else {
		frappe.msgprint("Start Date, End Date, Place Type and Travel Purpose not be selected before");
	}

}
