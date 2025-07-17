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
			"fieldname": "employee_name",
			"label": "Employee Name",
			"fieldtype": "Data",
			"options": "Employee Name",
			"width": 150,
		},
		{
			"fieldname": "types_of_separation",
			"label": "Types of Separation",
			"fieldtype": "Data",
			"options": "Types of Separation",
			"width": 150,
		},
		{
			"fieldname": "designation",
			"label": "Designation",
			"fieldtype": "Data",
			"options": "Designation",
			"width": 150,
		},
		{
			"fieldname": "employment_type",
			"label": "Employment Type",
			"fieldtype": "Data",
			"options": "Employment Type",
			"width": 150,
		},
		{
			"fieldname": "company",
			"label": "Company",
			"fieldtype": "Data",
			"options": "Company",
			"width": 150,
		},
		
	]

def get_data(filters=None):
	query = """
		SELECT
		    es.employee,
			es.employee_name,
			es.types_of_separation,
			e.designation,
			e.employment_type,
			e.company
		FROM 
			`tabEmployee Separation` AS es
		JOIN 
			`tabEmployee` AS e ON e.name = es.employee
		WHERE 
			es.docstatus = 1
				
	"""
	if filters.get("employee"):
		query += " and es.employee = \'" + str(filters.employee) + "\'"
	if filters.get("employment_type"):
		query += " and e.employment_type = \'" + str(filters.employment_type)+ "\'"	
	if filters.get("company"):
		query += " and e.company = \'" + str(filters.company) + "\'"			

	return  frappe.db.sql(query)
