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
			"fieldname": "employee",
			"label": "Employee ID",
			"fieldtype": "Data",
			"options": "Employee ID",
			"width": 150,
		},
		{
			"fieldname": "emp_name",
			"label": "Employee Name",
			"fieldtype": "Data",
			"options": "Employee Name",
			"width": 150,
		},
		{
			"fieldname":"date_of_joining",
			"label": "Date of Joining",
			"fieldtype": "Date",
			"options": "Date of Joining",
			"width": 150,
		},
		{
			"fieldname": "employee_type",
			"label": "Employment Type",
			"fieldtype": "Data",
			"options": "Employment Type",
			"width": 150,
		},
		{
			"fieldname": "old_designation",
			"label": "Old Designation",
			"fieldtype": "Data",
			"options": "Old Designation",
			"width": 150,
		},
		{
			"fieldname": "new_designation",
			"label": "New Designation",
			"fieldtype": "Data",
			"options": "New Designation",
			"width": 150,
		},
		{
			"fieldname": "transfer_type",
			"label": "Transfer Type",
			"fieldtype": "Data",
			"options": "Transfer Type",
			"width": 150,
		},
		{
			"fieldname": "transfer_date",
			"label": "Transfer Date",
			"fieldtype": "Date",
			"options": "Transfer Date",
			"width": 150,
		},
		{
			"fieldname": "old_branch",
			"label": "Old Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 150,
		},
		{
			"fieldname": "new_branch",
			"label": "New Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 150,
		},
		{
			"fieldname": "old_cost_center",
			"label": "Old Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150,
		},
		{
			"fieldname": "new_cost_center",
			"label": "New Cost Center",
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150,
		},
		{
			"fieldname": "old_division",
			"label": "Old Division",
			"fieldtype": "Link",
			"options": "Division",
			"width": 150,
		},
		{
			"fieldname": "new_division",
			"label": "New Division",
			"fieldtype": "Link",
			"options": "Division",
			"width": 150,
		},
		{
			"fieldname": "company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 150,
		}
		
	]

def get_data(filters=None):
	query = """
		SELECT
		    et.employee,
			et.emp_name,
			et.date_of_joining,
			et.employee_type,
			et.old_designation,
			et.new_designation,
			et.transfer_type,
			et.transfer_date,
			et.old_branch,
			et.new_branch,
			et.old_cost_center,
			et.new_cost_center,
			et.old_division,
			et.new_division,
			et.company
		FROM 
			`tabEmployee Transfer` AS et
		WHERE 
			et.docstatus = 1
	"""
	if filters.get("employee"):
		query += " and et.employee = \'" + str(filters.employee) + "\'"
	if filters.get("employee_type"):
		query += " and et.employee_type = \'" + str(filters.employee_type)+ "\'"	
	if filters.get("old_cost_center"):
		query += " and et.old_cost_center = \'" + str(filters.old_cost_center) + "\'"
	if filters.get("company"):
		query += " and et.company = \'" + str(filters.company) + "\'"			

	return  frappe.db.sql(query)

