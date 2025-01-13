// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Training And Development", {
// 	refresh(frm) {

// 	},
// });

cur_frm.add_fetch('employee_name','department','department');
cur_frm.add_fetch('employee_name','division','division');
cur_frm.add_fetch('employee_name','section','section');
cur_frm.add_fetch('employee_name','employee_group','employee_group');
cur_frm.add_fetch('employee_name','employee_subgroup','employee_subgroup');
cur_frm.add_fetch('employee_name','designation','designation');

frappe.ui.form.on("Training And Development", "end_date", function(frm) {
	if (frm.doc.end_date < get_today()) {
		msgprint(__("You can not select past date in End Date"));
		validated = false;
	}
	if (frm.doc.end_date < frm.doc.start_date) {
		msgprint(__("End Date should be greater than Start Date"));
		validated = false;
	}
});

frappe.ui.form.on("Training Fees", {
        "dsa_amount": function(frm, cdt, cdn){
                var child = locals[cdt][cdn];
                var dsa_percent;
                var amount;
                if(child.dsa_amount > 0){
                        dsa_percent=(child.dsa_percentage > 0)? child.dsa_percentage : 100;
                        amount = (dsa_percent/100) * child.dsa_amount;
                        frappe.model.set_value(child.doctype, child.name, "amount", amount);
                }
        },
        "dsa_percentage": function(frm, cdt, cdn){
                var child = locals[cdt][cdn];
                var dsa_percent, amount;
                dsa_percent = (child.dsa_percentage > 0)?child.dsa_percentage:100;
                amount = (child.dsa_percentage/100) * child.dsa_amount;
                frappe.model.set_value(child.doctype, child.name, "amount", amount);
        }
});

cur_frm.cscript.start_date = function(doc) {
	cur_frm.call({
		method: "hrms.hr.hr_custom_functions.get_date_diff",
	        args: { 
	            start_date: (typeof doc.start_date === 'undefined') ? null : doc.start_date,
	            end_date: (typeof doc.end_date === 'undefined') ? null : doc.end_date
	        },
	        callback: function(r) {
	            cur_frm.set_value("duration", r.message.toString() + " days");
	        }
	});
}

cur_frm.cscript.end_date = function(doc) {
	cur_frm.call({
		method: "hrms.hr.hr_custom_functions.get_date_diff",
		args: { 
	                start_date: (typeof doc.start_date === 'undefined') ? null : doc.start_date,
	                end_date: (typeof doc.end_date === 'undefined') ? null : doc.end_date
	        },
	        callback: function(r) {
	                cur_frm.set_value("duration", r.message.toString() + " days");
	        }
	});
}
