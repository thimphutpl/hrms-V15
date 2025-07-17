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
			"label": "ID",
			"fieldtype": "Link",
			"options": "Officiating Employee",
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
			"width": 200,
		},
		{
			"fieldname": "branch",
			"label": "Branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": 150,
		},
		{
			"fieldname": "officiate",
			"label": "Officiate Employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 150,
		},
		{
			"fieldname": "officiate_name",
			"label": "Officiate Employee Name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"width": 150,
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"width": 150,
		}

		
		
	]

def get_data(filters=None):
	query = """
		SELECT
	       oe.name,
		   oe.employee,
		   oe.employee_name,
		   oe.branch,
		   oe.officiate,
		   oe.officiate_name,
		   oe.from_date,
		   oe.to_date
		FROM 
			`tabOfficiating Employee` AS oe
		WHERE 
			oe.docstatus = 1
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

