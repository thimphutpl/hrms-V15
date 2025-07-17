# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(filters)
	return columns, data

def get_columns(filters):
	return [
		{
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": ("Employee"),
			"options": "Employee",
			"width": 150,
		},
		{
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"label": ("Employee Name"),
			"width": 150,
		},
		{
			"fieldname": "name",
			"fieldtype": "Link",
			"label": ("Transaction ID"),
			"width": 150,
			"options": "Overtime Application"
		},
		{
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"label": ("Cost Center"),
			"options": "Cost Center",
			"width": 150,
		},
		{
			"fieldname": "date",
			"fieldtype": "date",
			"label": ("Date"),
			"width": 150,
		},
		{
			"fieldname": "from_date",
			"fieldtype": "time",
			"label": ("From"),
			"width": 150,
		},
		{
			"fieldname": "to_date",
			"fieldtype": "time",
			"label": ("To"),
			"width": 150,
		},
		{
			"fieldname": "hrs",
			"fieldtype": "Dataq",
			"label": ("No of hours"),
			"width": 150,
		},
		{
			"fieldname": "normal_ot_type",
			"label": "Normal Hours",
			"fieldtype": "Data", 
			"width": 120
		},
		{
			"fieldname": "special_ot_type",
			"label": "Special Hours",
			"fieldtype": "Data", 
			"width": 120
		},
		
		{
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": ("Amount"),
			"width": 150,
		},
		{
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"label": ("Total Amount"),
			"width": 150
		}
		
	]


def get_data(filters):
	query ="""
		select ota.employee,ota.employee_name,ota.name,e.cost_center,otad.date,otad.from_date,otad.to_date,
		TIMESTAMPDIFF(MINUTE, otad.from_date, otad.to_date)/60 AS hrs,
	
		CASE 
			WHEN otad.is_late_night_ot = 0 THEN 'Normal'
			ELSE NULL
		END AS normal_ot_type,
		CASE 
			WHEN otad.is_late_night_ot = 1 THEN 'Special'
			ELSE NULL
		END AS special_ot_type,
		ota.total_amount,
		otad.amount
		from `tabOvertime Application Item` otad 
		Join `tabOvertime Application` ota On otad.parent=ota.name 
		Join `tabEmployee` e On ota.employee=e.name 
		where ota.docstatus =1
		"""
	if filters.get("employee"):
		query += " and ota.employee = '" + str(filters.employee) + "'"

	if filters.get("from_date") and filters.get("to_date"):
		query += " and otad.date between '{0}' and '{1}'".format(filters.get("from_date"), filters.get("to_date"))
	
	if filters.get("cost_center"):
		query += " and e.cost_center = \'" + str(filters.cost_center) + "\'"
	
	return frappe.db.sql(query)