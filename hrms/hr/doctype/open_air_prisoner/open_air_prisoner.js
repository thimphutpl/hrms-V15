// // // Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// // // For license information, please see license.txt

frappe.ui.form.on('Open Air Prisoner', {
	onload: function(frm) {
		if (!frm.doc.date_of_joining) {
			frm.set_value("date_of_joining", frappe.datetime.get_today());
		}
		frm.__branch_checked = false; // initialize flag
	},

	refresh: function(frm) {
		if (frm.doc.docstatus == 1 && frm.doc.status == "Left") {
			frm.add_custom_button(__("Unfreeze OAP"), function () {
				frm.trigger("unfreeze_oap");
			}, __("Unfreeze"));
		}
		frm.__branch_checked = false; // reset on refresh
	},

	unfreeze_oap: function(frm) {
		unfreeze_open_air_prisoner(frm);
	},

	branch: function(frm) {
		if (frm.__branch_checked) return; // prevent duplicate
		frm.__branch_checked = true;

		console.log("Branch changed to:", frm.doc.branch);
		validate_branch_change(frm, __("Please select date of transfer to new cost center"));
	}
});

function unfreeze_open_air_prisoner(frm) {
	frappe.call({
		method: "unfreeze_oap",
		doc: frm.doc,
		callback: function(r) {
			frm.set_value("status", r.message);
			frm.refresh_fields();
		}
	});
}

function validate_branch_change(frm, title) {
	console.log("Starting validation for branch:", frm.doc.branch);
	frappe.call({
		method: "erpnext.custom_utils.get_prev_doc",
		args: {
			doctype: frm.doctype,
			docname: frm.docname,
			col_list: "branch"
		},
		callback: function(r) {
			console.log("Server response:", r.message);
			if (frm.doc.branch && r.message && (frm.doc.branch !== r.message.branch)) {
				console.log("Branch changed from", r.message.branch, "to", frm.doc.branch);

				frm.set_df_property("date_of_transfer", "hidden", 0);
				frappe.prompt({
					fieldtype: "Date",
					fieldname: "date_of_transfer",
					reqd: 1,
					description: __("*This information shall be recorded in employee internal work history.")
				}, function(data) {
					frm.set_value("date_of_transfer", data.date_of_transfer);
					frm.refresh_field("date_of_transfer");
				}, title, __("Update"));
			}
		}
	});
}
