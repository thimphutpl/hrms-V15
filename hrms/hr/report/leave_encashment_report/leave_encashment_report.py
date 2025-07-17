# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns= get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"fieldname": "name",
			"label": "Leave Encashment ID",
			"fieldtype": "Link",
			"options": "Leave Encashment",
			"width": 150,
		},
		{
			"fieldname": "employee",
			"label": "Employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150,
		},
		{
			"fieldname": "employee_name",
			"label": "Employee Name",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "designation",
			"label": "Designation",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "division",
			"label": "Division",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "encashment_date",
			"label": "Encashment Date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"fieldname": "leave_type",
			"label": "Leave Type",
			"fieldtype": "Link",
			"options": "Leave Type",
			"width": 150,
		},
		{
			"fieldname": "basic_pay",
			"label": "Basic Pay",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 150,
		},
		{
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150,
		}
	]

def get_data(filters=None):
	query = """
		SELECT
		le.name,
		le.employee,
		le.employee_name,
		le.designation,
		le.division,
		le.encashment_date,
		le.leave_type,
		le.basic_pay,
		le.branch,
		le.cost_center
		FROM 
			`tabLeave Encashment` AS le
		WHERE 
			le.docstatus = 0
		"""
	if filters.get("employee"):
		query += " and le.employee = \'" + str(filters.employee)+ "\'"	

	if filters.get("company"):
		query += " and le.company = \'" + str(filters.company) + "\'"		
	return  frappe.db.sql(query)
