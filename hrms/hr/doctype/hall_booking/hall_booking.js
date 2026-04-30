// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('Hall Booking', {
	refresh: function(frm) {
		if(!frm.doc.posting_date) {
			frm.set_value("posting_date", get_today())
		}
		frm.events.show_general_ledger(frm);
		if (frm.doc.docstatus==1) {
			frm.add_custom_button(__('Payment'),function(){
				frappe.model.open_mapped_doc({
					method: "hrms.hr.doctype.hall_booking.hall_booking.make_direct_payment",
					frm: frm
				})
			},__("Payment"));
		}

	},
	no_of_days: function(frm) {
		calculate_amount(frm);
	},
	rate: function(frm) {
		calculate_amount(frm);
	},
	"from_date": function(frm) {
		calculate_amount(frm);
	},
	"to_date": function(frm) {
		calculate_amount(frm);	
	},
	function(frm) {
		calculate_amount(frm);	
	},
	show_general_ledger: function(frm) {
		if(frm.doc.docstatus==1) {
			frm.add_custom_button(__('Ledger'), function() {
				frappe.route_options = {
					"voucher_no": frm.doc.name,
					"from_date": frm.doc.posting_date,
					"to_date": frm.doc.posting_date,
					"company": frm.doc.company,
					group_by_voucher: 0
				};
				frappe.set_route("query-report", "General Ledger");
			});
		}
	},
	make_direct_payment: function() {
		frappe.model.open_mapped_doc({
			method: "erpnext.hr.doctype.hall_booking.hall_booking.make_direct_payment",
			frm: cur_frm
		})
	},

});


function calculate_amount(frm) {
	if(frm.doc.to_date && frm.doc.from_date){
		var date1 = new Date(frm.doc.from_date);
		var date2 = new Date(frm.doc.to_date);
		if(date1 > date2){
			frappe.msgprint("To date Cannot be before From Date ");
		}
	
		// var timeDiff = Math.abs(date2.getTime() - date1.getTime());
		// var diffDays = Math.ceil(timeDiff / (1000 * 3600 * 24)); 
		// cur_frm.set_value("no_of_days", diffDays + 1);
		if(frm.doc.rate && frm.doc.no_of_days){
			cur_frm.set_value("amount", frm.doc.no_of_days * frm.doc.rate);
		}
	}
}