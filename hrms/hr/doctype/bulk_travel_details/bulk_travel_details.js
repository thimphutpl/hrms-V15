// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Travel Details", {
	refresh(frm) {
		frm.fields_dict["employees"].grid.get_field("employee").get_query = function (doc, cdt, cdn) {
            return {
                filters: {
                    company: frm.doc.company
                }
            };
        };
        if (frm.doc.docstatus == 0 && !frm.doc.bulk_travel_claim) {
				if (!frm.doc.bulk_travel_claim) {
					frm.add_custom_button(__("Bulk Travel Claim"), function () {
						frm.trigger("create_bulk_travel_claim");
						},
						__("Create")
					);
				}
			// }
		}

	},
    create_bulk_travel_claim: function (frm) {
		frappe.model.open_mapped_doc({
			method: "hrms.hr.doctype.bulk_travel_details.bulk_travel_details.make_bulk_travel_claim",
			frm: cur_frm
		})
	},
});
