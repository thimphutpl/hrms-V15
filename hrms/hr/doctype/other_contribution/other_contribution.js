// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Other Contribution', {
	setup: function(frm) {
		frm.get_docfield("items").allow_bulk_edit = 1;
		frm.get_field('items').grid.editable_fields = [
				{fieldname: 'employee', columns: 3},
				{fieldname: 'employee_grade', columns: 1},
				{fieldname: 'designation', columns: 2},
				{fieldname: 'branch', columns: 2},
				{fieldname: 'contribution', columns: 2},
		];
	},
	onload: function(frm){
		employee_details(frm);
		total_html(frm);
		if(frm.doc.__islocal){
			update_data(frm.doc, "remove_employee");
		}
	},
	refresh: function(frm) {
		cur_frm.set_query("group_cost_center", function() {
                return {
                    "filters": {
                        "disabled": 0,
                        "list_in_other_contribution": 1
                    }
                };
		});
		cur_frm.set_query("contributing_branch", function (frm) {
			return {
				query:"hrms.hr.doctype.other_contribution.other_contribution.get_branches",
				filters: {
					"parent_cost_center": cur_frm.doc.group_cost_center
				}
			}
	});
		

		employee_details(frm);
		total_html(frm);
	},
	group_cost_center: function(frm){
		cur_frm.set_value("contributing_branch",null)
	},
	employee: function(frm){
		employee_details(frm);
		//update_data(frm.doc, "remove_employee");
	},
	get_employees: function(frm) {
		update_data(frm.doc, "get_employees");
	},
	contribution_type: function(frm){
		update_data(frm.doc, "update_amounts");
	},
	contribution: function(frm){
		update_data(frm.doc, "update_amounts");
	},
	total_contribution_amount: function(){
		total_html(frm);
	}
});

// frappe.ui.form.on('Other Contribution', function(frm){

// });

var update_data=function(doc, method){
	cur_frm.call({
		method: method,
		doc:doc
	});
}

var employee_details = function(frm){
	if(frm.doc.employee){
		$(cur_frm.fields_dict.employee_details.wrapper).html("<b>"+(frm.doc.salutation ? frm.doc.salutation+". " : frm.doc.salutation)+frm.doc.employee_name+"<br>"+frm.doc.designation+" ("+frm.doc.employee_grade+")"+"<br>"+'<a href="/desk#Form/Branch/'+frm.doc.employee_branch+'">'+frm.doc.employee_branch+"</a>"+"</b>");
	} else {
		$(cur_frm.fields_dict.employee_details.wrapper).html('');
	}
}

var total_html = function(frm){
	if(frm.doc.total_contribution_amount > 0){
		$(cur_frm.fields_dict.total_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Total No.of Contributors</label><br><b>'+frm.doc.total_noof_contributors+"/"+frm.doc.total_noof_employees+'</b>');
	} else {
		$(cur_frm.fields_dict.total_html.wrapper).html('<label class="control-label" style="padding-right: 0px;">Total No.of Contributors</label><br><b>'+'</b>');
	}
}
