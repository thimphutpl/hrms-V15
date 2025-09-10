// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Muster Roll Transfer", {
    onload(frm) {
        frm.set_query("employee", "items", function () {
            return {
                filters: {
                    'status': 'Active',
                    'branch': frm.doc.branch
                }
            }
        });

        frm.set_query("to_branch", "items", function () {
            return {
                filters: {
                    'name': ["!=", frm.doc.branch]
                }
            }
        });
    },

	refresh(frm) {
        if (frm.doc.docstatus != 1 && !frm.is_new()) {
			frm.add_custom_button(__("Get Employees"), function () {
				frm.events.get_employee_details(frm);
			}).toggleClass("btn-primary", !(frm.doc.items || []).length);
		}
	},

    branch: function(frm) {
        frm.events.clear_employee_table(frm);
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
				if (r.docs?.[0]?.items) {
					frm.dirty();
					frm.save();
				}

				frm.refresh();

				frm.scroll_to_field("items");
			});
    },

    clear_employee_table: function (frm) {
		frm.clear_table("items");
		frm.refresh();
	},
});
