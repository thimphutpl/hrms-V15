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
			"fieldname": "name",
			"label": "ID",
			"fieldtype": "Link",
			"options": "Leave Travel Concession",
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
			"options": "Employee Name",
			"width": 150,
		},
		{
			"fieldname": "bank_name",
			"label": "Bank Name",
			"fieldtype": "Data",
			"options": "Bank Name",
			"width": 150,
		},
		{
			"fieldname": "bank_ac_no",
			"label": "Bank Account Number",
			"fieldtype": "Data",
			"options": "Bank Account Number",
			"width": 150,
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150,
		}
		
	]

def get_data(filters=None):
	query = """
		SELECT
		    ltc.name,
			ltc.fiscal_year,
			ld.employee,
			ld.employee_name,
			ld.bank_name,
			ld.bank_ac_no,
			ld.amount
		FROM 
			`tabLeave Travel Concession` AS ltc
		JOIN 
			`tabLTC Details` AS ld ON ld.parent = ltc.name	
		WHERE 
			ltc.docstatus = 1
	"""	
	if filters.get("fiscal_year"):
		query += " and ltc.fiscal_year = \'" + str(filters.fiscal_year)+ "\'"	
	if filters.get("branch"):
		query += " and ltc.branch = \'" + str(filters.branch) + "\'"		
	return  frappe.db.sql(query)

