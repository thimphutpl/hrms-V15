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
			"fieldname": "name",
			"label": "TC name",
			"fieldtype": "Data",
			"options": "TC name",
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
			"fieldname": "cost_center",
			"label": "Cost Center",
			"fieldtype": "Data",
			"options": "Cost Center",
			"width": 150,
		},
		{
			"fieldname": "division",
			"label": "Department",
			"fieldtype": "Data",
			"options": "Department",
			"width": 150,
		},
		{
			"fieldname": "from_date",
			"label": "From",
			"fieldtype": "Data",
			"options": "From",
			"width": 150,
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Data",
			"options": "To Date",
			"width": 150,
		},
		{
			"fieldname": "no_days",
			"label": "NO Of Days",
			"fieldtype": "Data",
			"options": "NO Of Days",
			"width": 150,
		},
		{
			"fieldname": "place_type",
			"label": "Place Type",
			"fieldtype": "Data",
			"options": "Place Type",
			"width": 150,
		},
		{
			"fieldname": "month_name",
			"label": "Month",
			"fieldtype": "Month",
			"options": "Month",
			"width": 150,
		},
		{
			"fieldname": "dsa_per_day",
			"label": "DSA Per Day",
			"fieldtype": "Currency",
			"options": "DSA Per Day",
			"width": 150,
		},
			{
			"fieldname": "total_claim_amount",
			"label": "Total Claim",
			"fieldtype": "Currency",
			"options": "Total Claim",
			"width": 150,
		},
	]

def get_data(filters=None):
	query = """
		SELECT
		    etc.employee,
			etc.employee_name,
			etc.name,
			etc.designation,
			etc.cost_center,
			etc.division,
			tci.from_date,
			tci.to_date,
			tci.no_days,
			etc.place_type,
			MONTHNAME(etc.posting_date) AS month_name,
			etc.dsa_per_day,
			etc.total_claim_amount

		FROM 
			`tabTravel Claim` AS etc 
		JOIN 
			`tabTravel Claim Item` AS tci ON tci.parent = etc.name
		WHERE 
			etc.docstatus = 1
	"""
	if filters.get("cost_center"):
		query += " and etc.cost_center = \'" + str(filters.cost_center) + "\'"
	if filters.get("from_date") and filters.get("to_date"):
		query += " and tci.from_date = '{0}' and tci.to_date = '{1}'".format(
			filters.get("from_date"), filters.get("to_date")
		)
	if filters.get("employee"):
		query += " and etc.employee = \'"+str(filters.employee) + "\'"
	if filters.get("month"):
		query += " and etc.posting_date = \'" + str(filters.month) + "\'"		

	return  frappe.db.sql(query)
