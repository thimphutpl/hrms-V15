// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Muster Roll Payment Entry", {
    onload(frm) {
		frm.ignore_doctypes_on_cancel_all = ["Pay Slip", "Journal Entry"];

        let grid = frm.fields_dict['employees'].grid;
        grid.cannot_add_rows = true;
    },
	refresh(frm) {
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.page.clear_primary_action();
			frm.add_custom_button(__("Get Employees"), function () {
				frm.events.get_employee_details(frm);
			}).toggleClass("btn-primary", !(frm.doc.employees || []).length);
		}

        if (
			(frm.doc.employees || []).length &&
			!frappe.model.has_workflow(frm.doctype) &&
			!cint(frm.doc.payment_slips_created) &&
			frm.doc.docstatus != 2
		) {
			if (frm.doc.docstatus == 0 && !frm.is_new()) {
				frm.page.clear_primary_action();
				frm.page.set_primary_action(__("Create Pay Slips"), () => {
					frm.save("Submit").then(() => {
						frm.page.clear_primary_action();
						frm.refresh();
					});
				});
			} else if (frm.doc.docstatus == 1 && frm.doc.status == "Failed") {
				frm.add_custom_button(__("Create Pay Slips"), function () {
					frm.call("create_pay_slips");
				}).addClass("btn-primary");
			}
		}

		if (frm.doc.docstatus == 1) {
			if (frm.custom_buttons) frm.clear_custom_buttons();
			frm.events.add_context_buttons(frm);
		}
	},

    create_pay_slips: function (frm) {
        frm.call({
            doc: frm.doc,
            method: "run_doc_method",
            args: {
                method: "create_pay_slips",
                dt: "Muster Roll Payment Entry",
                dn: frm.doc.name,
            },
        });
    },

	add_context_buttons: function (frm) {
		if (
			frm.doc.pay_slips_submitted ||
			(frm.doc.__onload && frm.doc.__onload.submitted_ss)
		) {
			frm.events.add_bank_entry_button(frm);
		} else if (frm.doc.pay_slips_created && frm.doc.status !== "Queued") {
			frm.add_custom_button(__("Submit Pay Slip"), function () {
				submit_pay_slip(frm);
			}).addClass("btn-primary");
		} else if (!frm.doc.pay_slips_created && frm.doc.status === "Failed") {
			frm.add_custom_button(__("Create Pay Slips"), function () {
				frm.trigger("create_pay_slips");
			}).addClass("btn-primary");
		}
	},

	add_bank_entry_button: function (frm) {
		frm.call("has_bank_entries").then((r) => {
			if (!r.message.has_bank_entries) {
				frm.add_custom_button(__("Make Bank Entry"), function () {
					make_bank_entry(frm);
				}).addClass("btn-primary");
			}
		});
	},

    processing_branch: function(frm) {
        frm.events.clear_employee_table(frm);
    },

	month: function (frm) {
		frm.trigger("set_start_end_dates").then(() => {
			frm.events.clear_employee_table(frm);
		});
	},

	set_start_end_dates: function (frm) {
		frappe.call({
			method: "hrms.payroll.doctype.payroll_entry.payroll_entry.get_start_end_dates",
			args: {
				fiscal_year: frm.doc.fiscal_year,
				month: frm.doc.month,
			},
			callback: function (r) {
				if (r.message) {
					in_progress = true;
					frm.set_value("start_date", r.message.start_date);
					frm.set_value("end_date", r.message.end_date);
				}
			},
		});
	},

    get_employee_details: function (frm) {
        return frappe
			.call({
				doc: frm.doc,
				method: "fill_employee_details",
				freeze: true,
				freeze_message: __("Fetching Employees"),
			})
			.then((r) => {
				if (r.docs?.[0]?.employees) {
					frm.dirty();
					frm.save();
				}

				frm.refresh();
				render_employee_attendance(frm, r.message);
				frm.scroll_to_field("employees");
			});
    },

    clear_employee_table: function (frm) {
		frm.clear_table("employees");
		frm.refresh();
	},
});

let make_bank_entry = function (frm) {
	const doc = frm.doc;
	return frappe.call({
		method: "run_doc_method",
		args: {
			method: "make_bank_entry",
			dt: "Muster Roll Payment Entry",
			dn: frm.doc.name,
		},
		callback: function () {
			frappe.set_route(
				'List', 'Journal Entry', {"reference_type": frm.doc.doctype, "reference_name": frm.doc.name}
			);
		},
		freeze: true,
		freeze_message: __("Creating Payment Entries......"),
	});
};

let render_employee_attendance = function (frm, data) {
	frm.fields_dict.attendance_detail_html.html(
		frappe.render_template("mr_employees_with_unmarked_attendance", {
			data: data,
		}),
	);
};

// Submit salary slips

const submit_pay_slip = function (frm) {
	frappe.confirm(
		__(
			"This will submit Pay Slips and create accrual Journal Entry. Do you want to proceed?",
		),
		function () {
			frappe.call({
				method: "submit_pay_slips",
				args: {},
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Submitting Pay Slips and creating Journal Entry..."),
			});
		},
		function () {
			if (frappe.dom.freeze_count) {
				frappe.dom.unfreeze();
			}
		},
	);
};
