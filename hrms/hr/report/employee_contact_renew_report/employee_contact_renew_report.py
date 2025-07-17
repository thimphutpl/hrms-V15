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
			"fieldname": "grade",
			"label": "Grade",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "basic_salary",
			"label": "Basic Salary",
			"fieldtype": "Currency",
			"width": 150,
		}
	]

def get_data(filters=None):
	query = """
		SELECT
		cra.employee,
		cra.employee_name,
		cra.designation,
		cra.division,
		cra.grade,
		cra.basic_salary
		FROM 
			`tabContract Renewal Application` AS cra
		WHERE 
			cra.docstatus = 1
		"""	
	if filters.get("from_date") and filters.get("to_date"):
		query += " and oe.from_date <= '{1}' and oe.to_date >= '{0}'".format(filters.get("from_date"), filters.get("to_date"))
	if filters.get("employee"):
		query += " and oe.employee = \'" + str(filters.employee)+ "\'"	
	if filters.get("officiate"):
		query += " and oe.officiate = \'" + str(filters.officiate) + "\'"
	if filters.get("company"):
		query += " and oe.company = \'" + str(filters.company) + "\'"		
	return  frappe.db.sql(query)
