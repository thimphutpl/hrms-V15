// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Travel Adjustment", {
	setup: function(frm) {
        frm.set_query("employee", function() {
            return erpnext.queries.employee();
        });
    },
	
	refresh(frm) {

	},
});

frappe.ui.form.on("Travel Adjustment Item", {
    from_date: function(frm, cdt, cdn) {
        frappe.model.set_value(cdt, cdn, "to_date", null);
        set_form_data(frm, cdt, cdn);
    },

    halt: function (frm, cdt, cdn) {
		var item = locals[cdt][cdn]
		cur_frm.toggle_reqd("to_date", item.halt);
	},

    to_date: function(frm, cdt, cdn) {
        set_form_data(frm, cdt, cdn);
    },

    country: function(frm, cdt, cdn) {
        set_form_data(frm, cdt, cdn);
    }, 

    exchange_rate: function(frm, cdt, cdn) {
        set_form_data(frm, cdt, cdn);
    },

});

function set_form_data(frm, cdt, cdn) {
    set_employee_dsa(frm, cdt, cdn);
	calculate_total_dsa(frm, cdt, cdn);
    refresh_fields(frm);
}

const set_employee_dsa = (frm, cdt, cdn) => {
	if (frm.doc.employee) {
		let child = locals[cdt][cdn];

		if (!child.country || !frm.doc.grade) {
			return;
		}

		frappe.call({
			method: "hrms.hr.doctype.travel_authorization.travel_authorization.get_employee_dsa",
			args: {
				country: child.country,
				grade: frm.doc.grade,
			},
			callback: function(r) {					
				if (r.message && r.message.length > 0) {
					frappe.model.set_value(cdt, cdn, "dsa", r.message[0].dsa);
					frappe.model.set_value(cdt, cdn, "currency", r.message[0].currency);
				} else {
					frappe.model.set_value(cdt, cdn, "dsa", "");
					frappe.model.set_value(cdt, cdn, "currency", "");
				}
			},
		});
	}
};

function calculate_total_dsa(frm, cdt, cdn) {
    var item = locals[cdt][cdn];
	if (!item.exchange_rate) {
		item.exchange_rate = 1
	}
    if (item.dsa && item.no_days) {
		if (item.to_date && item.from_date) {
			frappe.model.set_value(cdt, cdn, "no_days", 1 + cint(frappe.datetime.get_day_diff(item.to_date, item.from_date)))
		} else {
			frappe.model.set_value(cdt, cdn, "no_days", 1)	
		}
		frappe.model.set_value(cdt, cdn, "dsa_nu_per_day", flt(item.dsa) * flt(item.exchange_rate))
        frappe.model.set_value(cdt, cdn, "total_dsa", flt(item.dsa_nu_per_day) * flt(item.no_days));
    }
}

function refresh_fields(frm) {
	frm.refresh_field("items");
}