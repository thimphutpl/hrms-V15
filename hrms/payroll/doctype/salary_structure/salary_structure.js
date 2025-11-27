// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Salary Structure", { 
	onload: function (frm) {
		frm.set_query("salary_component", "earnings", function () {
			return {
				filters: { type: "earning", company: frm.doc.company },
			};
		});
		frm.set_query("salary_component", "deductions", function () {
			return {
				filters: { type: "deduction", company: frm.doc.company },
			};
		});
	},

	// Payment Method handlers - These are used in Python calculations
	contract_allowance_method: function(frm){
		calculate_others(frm);
	},
	corporate_allowance_method: function(frm){
		calculate_others(frm);
	},
	mvc_method: function(frm){
		calculate_others(frm);
	},

	// Payment Value handlers - These are used in Python calculations
	contract_allowance: function(frm){
		calculate_others(frm);
	},
	corporate_allowance: function(frm){
		calculate_others(frm);
	},
	mvc: function(frm){
		calculate_others(frm);
	},

	// Only keep the eligibility fields that are actually referenced in Python
	// Based on the Python code, these fields are checked via dynamic mapping
	eligible_for_fixed_allowance: function(frm){
		calculate_others(frm);
	},
	eligible_for_pf: function(frm){
		calculate_others(frm);
	},
	eligible_for_gis: function(frm){
		calculate_others(frm);
	},
	eligible_for_sws: function(frm){
		calculate_others(frm);
	},
	eligible_for_health_contribution: function(frm){
		calculate_others(frm);
	},
	eligible_for_hra: function(frm){
		calculate_others(frm);
	},
});

function calculate_others(frm) {
	frappe.call({
		method: "update_salary_structure",
		doc: frm.doc,
		args: {
			"remove_flag": 0
		},
		callback: function (r) {
			if (r.message) {
				// Remove earnings
				if (frm.doc.earnings) {
					frm.doc.earnings.forEach(function (i, j) {
						r.message.forEach(function (k, l) {
							if (k.name == i.name) {
								cur_frm.get_field("earnings").grid.grid_rows[j].remove();
							}
						})
					})
				}

				// Remove deductions
				if(frm.doc.deductions){
					frm.doc.deductions.forEach(function(i,j){
						r.message.forEach(function(k,l){
							if(k.name==i.name){
								cur_frm.get_field("deductions").grid.grid_rows[j].remove();
							}
						})
					});
				}
			}
			frm.refresh_fields()
		},
		freeze: true,
		freeze_message: "Recalculating ..."
	})
}