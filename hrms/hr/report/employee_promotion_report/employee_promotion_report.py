# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe


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
			"fieldname": "current_grade",
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
		    ep.employee,
			ep.employee_name,
			e.designation,
			e.employment_type,
			e.company
		FROM 
			`tabEmployee Promotion` AS ep 
		JOIN 
			`tabEmployee Property History` AS eph ON eph.parent = ep.name
		JOIN 
			`tabEmployee` AS e ON e.name = ep.employee
		WHERE 
			ep.docstatus = 1
	  	AND eph.property = 'designation'					
	"""
	if filters.get("fiscal_year"):
		query += " and ep.fiscal_year = \'" + str(filters.fiscal_year) + "\'"
	if filters.get("month"):
		query += " and ep.month = \'" + str(filters.month) + "\'"
	if filters.get("employee"):
		query += " and ep.employee = \'" + str(filters.employee) + "\'"
	if filters.get("employment_type"):
		query += " and e.employment_type = \'" + str(filters.employment_type)+ "\'"	
	if filters.get("cost_center"):
		query += " and e.cost_center = \'" + str(filters.cost_center) + "\'"
	if filters.get("company"):
		query += " and e.company = \'" + str(filters.company) + "\'"			

	return  frappe.db.sql(query)
