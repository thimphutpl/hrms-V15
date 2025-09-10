// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Leave Encashment", {
	onload: function (frm) {
		// Ignore cancellation of doctype on cancel all.
		frm.ignore_doctypes_on_cancel_all = ["Leave Ledger Entry"];
	},
	setup: function (frm) {
		frm.set_query("leave_type", function () {
			return {
				filters: {
					allow_encashment: 1,
				},
			};
		});
		frm.set_query("leave_period", function () {
			return {
				filters: {
					is_active: 1,
				},
			};
		});
	},
	refresh: function (frm) {
		refresh_html(frm);
		
		cur_frm.set_intro("");
		if (frm.doc.__islocal && !frappe.user_roles.includes("Employee")) {
			frm.set_intro(__("Fill the form and save it"));
		}

		hrms.leave_utils.add_view_ledger_button(frm);
	},
	employee: function (frm) {
		if (frm.doc.employee) {
			frappe.run_serially([
				() => frm.trigger("get_employee_currency"),
				() => frm.trigger("get_leave_details_for_encashment"),
			]);
		}
	},
	leave_type: function (frm) {
		frm.trigger("get_leave_details_for_encashment");
	},
	encashment_date: function (frm) {
		frm.trigger("get_leave_details_for_encashment");
	},
	get_leave_details_for_encashment: function (frm) {
		frm.set_value("actual_encashable_days", 0);
		frm.set_value("encashment_days", 0);

		if (frm.doc.docstatus === 0 && frm.doc.employee && frm.doc.leave_type) {
			return frappe.call({
				method: "get_leave_details_for_encashment",
				doc: frm.doc,
				callback: function (r) {
					frm.refresh_fields();
				},
			});
		}
	},

	get_employee_currency: function (frm) {
		frappe.call({
			method: "hrms.payroll.doctype.salary_structure.salary_structure.get_employee_currency",
			args: {
				employee: frm.doc.employee,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_value("currency", r.message);
					frm.refresh_fields();
				}
			},
		});
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
