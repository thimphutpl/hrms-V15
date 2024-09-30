// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Payment Request", {
	setup: function(frm) {
		frm.set_query("business_activity", function () {
			return {
				query: "hrms.hr.doctype.travel_payment_request.travel_payment_request.get_business_activities",
				filters: {
					company: frm.doc.company,
				}
			};
		});
	},

	refresh(frm) {
		frm.set_query("branch", function(doc){
			return {
				filters: {
					'company': doc.company,
				}
			}
		});
	},

    calculate_total: function (frm) {
		let total = 0
		frm.doc.items.forEach((item) => {
			total += item.amount;
		});

		frm.set_value({
			total_amount: flt(total),
		});
	},
});

frappe.ui.form.on("Travel Payment Request Item", {
	calculate: function (frm, cdt, cdn) {
		frm.trigger("calculate_total");
	},
	amount: function (frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},
});