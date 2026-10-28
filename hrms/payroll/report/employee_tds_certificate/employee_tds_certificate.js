// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Employee TDS Certificate"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"on_change": function (query_report) {
				// Company change invalidates employee selection
				query_report.set_filter_value("employee", null);
				query_report.set_filter_value("e_name", null);
				query_report.set_filter_value("cid", null);
				query_report.set_filter_value("tpn", null);
			}
		},
		{
			"fieldname": "employee_group",
			"label": __("Employee Group"),
			"fieldtype": "Link",
			"options": "Employee Group",
			"description": __("Health Contribution column is shown only for NAS (RBA) employees"),
			"on_change": function (query_report) {
				// Clear employee selection when group changes
				query_report.set_filter_value("employee", null);
				query_report.set_filter_value("e_name", null);
				query_report.set_filter_value("cid", null);
				query_report.set_filter_value("tpn", null);
			}
		},
		{
			"fieldname": "fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"default": frappe.defaults.get_user_default("fiscal_year"),
		},
		// {
		// 	"fieldname": "employee",
		// 	"label": __("Employee"),
		// 	"fieldtype": "Link",
		// 	"options": "Employee",
		// 	"reqd": 1,
		// 	"on_change": function (query_report) {
		// 		var emp = query_report.get_values().employee;
		// 		if (!emp) {
		// 			return;
		// 		}
		// 		frappe.model.with_doc("Employee", emp, function (r) {
		// 			var fy = frappe.model.get_doc("Employee", emp);
		// 			frappe.query_report.set_filter_value("e_name", fy.employee_name);
		// 			frappe.query_report.set_filter_value("cid", fy.passport_number);
		// 			frappe.query_report.set_filter_value("tpn", fy.tpn_number);
		// 			frappe.query_report.refresh();
		// 		});
		// 		frappe.call({
		// 			method: "frappe.client.get_single_value",
		// 			args: {
		// 				doctype: "HR Settings",
		// 				field: "seal",
		// 			},
		// 			callback: function (r) {
		// 				console.log(r.message);
		// 				frappe.query_report.set_filter_value("seal", r.message);
		// 				frappe.query_report.refresh();
		// 			}
		// 		});
		// 	}
		// },
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"reqd": 1,
			"get_query": function () {
				var employee_group = frappe.query_report.get_filter_value("employee_group");
				return {
					filters: {
						"employee_group": employee_group || ""
					}
				};
			},
			"on_change": function (query_report) {
				var emp = query_report.get_values().employee;
				if (!emp) {
					return;
				}
				frappe.model.with_doc("Employee", emp, function (r) {
					var fy = frappe.model.get_doc("Employee", emp);
					frappe.query_report.set_filter_value("e_name", fy.employee_name);
					frappe.query_report.set_filter_value("cid", fy.passport_number);
					frappe.query_report.set_filter_value("tpn", fy.tpn_number);
					frappe.query_report.refresh();
				});
				frappe.call({
					method: "frappe.client.get_single_value",
					args: {
						doctype: "HR Settings",
						field: "seal",
					},
					callback: function (r) {
						console.log(r.message);
						frappe.query_report.set_filter_value("seal", r.message);
						frappe.query_report.refresh();
					}
				});
			}
		},
		{
			"fieldname": "e_name",
			"fieldtype": "Data",
			"label": __("Employee Name"),
			"read_only": 1
		},
		{
			"fieldname": "cid",
			"fieldtype": "Data",
			"label": __("CID"),
			"read_only": 1
		},
		{
			"fieldname": "tpn",
			"fieldtype": "Data",
			"label": __("TPN"),
			"read_only": 1
		},
		// {
		// 	"fieldname": "approver",
		// 	"label": "Approver",
		// 	"fieldtype": "Link",
		// 	"options": "Employee",
		// 	"on_change": function (query_report) {
		// 		var emp = query_report.get_values().approver;
		// 		if (!emp) {
		// 			return;
		// 		}
		// 		frappe.model.with_doc("Employee", emp, function (r) {
		// 			var fy = frappe.model.get_doc("Employee", emp);
		// 			frappe.query_report.set_filter_value("approver_name", fy.employee_name);
		// 			frappe.query_report.set_filter_value("approver_designation", fy.designation);
		// 			frappe.query_report.refresh();
		// 		});
		// 	}
		// },
		// {
		// 	"fieldname": "approver_name",
		// 	"label": "Approver Name",
		// 	"fieldtype": "Data",
		// 	"read_only": 1

		// },
		// {
		// 	"fieldname": "approver_designation",
		// 	"label": "Approver Designation",
		// 	"fieldtype": "Data",
		// 	"read_only": 1
		// },
		{
			"fieldname": "seal",
			"label": "Seal and Signature",
			"fieldtype": "Data",
			"read_only": 1,
			"hidden": 1
		}


	],
	onload: function (report) {
		report.page.add_inner_button("Clear Filters", function () {
			report.set_filter_value("company", null);
			report.set_filter_value("fiscal_year", null);
			report.set_filter_value("employee_group", null);
			report.set_filter_value("employee", null);
			report.set_filter_value("e_name", null);
			report.set_filter_value("cid", null);
			report.set_filter_value("tpn", null);

		});
	},
	
};
