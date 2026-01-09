
// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Encashment', {
	onload: function(frm) {
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];
	},

	setup: function(frm) {
		frm.set_query("leave_type", function() {
			return {
				filters: {
					allow_encashment: 1
				}
			};
		});

		frm.set_query("leave_period", function() {
			const dt = frm.doc.encashment_date || frappe.datetime.get_today();
			const company = frm.doc.company;

			let filters = {
				is_active: 1
			};

			if (company) {
				filters.company = company;
			}

			if (dt) {
				filters.from_date = ["<=", dt];
				filters.to_date = [">=", dt];
			}

			return { filters };
		});
	},

	refresh: function(frm) {
		cur_frm.set_intro("");
		if (frm.doc.__islocal && !in_list(frappe.user_roles, "Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		}

		if (frm.docstatus == 1) {
			frm.add_custom_button(
				__("Payment Entry"),
				function () {
				},
				__('Create')
			);
		}
	},

	employee: function(frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger('get_leave_details_for_encashment')
			]);
		}
	},

	leave_type: function(frm) {
		frm.trigger("get_leave_details_for_encashment");
	},

	encashment_date: function(frm) {
		frm.refresh_field("leave_period");
		frm.trigger("get_leave_details_for_encashment");
	},

	company: function(frm) {
		frm.refresh_field("leave_period");
	},

	get_leave_details_for_encashment: function(frm) {
		if (frm.doc.docstatus == 0 && frm.doc.employee && frm.doc.leave_type) {
			return frappe.call({
				method: "get_leave_details_for_encashment",
				doc: frm.doc,
				callback: function(r) {
					frm.refresh_fields();
				}
			});
		}
	},
});
