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
			"label": "Name",
			"fieldtype": "Link",
			"options": "Salary Increment",
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
			"fieldname": "employee",
			"label": "Employee ID",
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
			"fieldname": "fiscal_year",
			"label": "Fiscal Year",
			"fieldtype": "Data",
			"options": "Fiscal Year",
			"width": 150,
		},
		{
			"fieldname": "month",
			"label": "Month",
			"fieldtype": "Data",
			"options": "Month",
			"width": 150,
		},
		{
			"fieldname": "old_basic",
			"label": "Current Basic",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": "increment",
			"label": "Increment",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		},
		{
			"fieldname": "new_basic",
			"label": "New Basic",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		}
		
		
	]

def get_data(filters=None):
	query = """
		SELECT
			si.name,
			si.branch,
			si.employee,
			si.employee_name,
			si.fiscal_year,
			si.month,
			si.old_basic,
			si.increment,
			si.new_basic
		FROM 
			`tabSalary Increment` AS si
		WHERE 
		 	si.docstatus < 2	
	"""
	if filters.get("docstatus"):
		query += " and si.docstatus = \'" + str(filters.docstatus) + "\'"
	if filters.get("branch"):
		query += " and si.branch = \'" + str(filters.branch)+ "\'"	
	if filters.get("fiscal_year"):
		query += " and si.fiscal_year = \'" + str(filters.fiscal_year) + "\'"
	if filters.get("month"):
		query += " and si.month = \'" + str(filters.month) + "\'"			

	return  frappe.db.sql(query)

