// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Payment Request", {
	refresh(frm) {

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