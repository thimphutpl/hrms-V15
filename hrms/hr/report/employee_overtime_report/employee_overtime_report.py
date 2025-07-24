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
			"fieldname": "hours",
			"fieldtype": "Data",
			"label": ("No of Hours"),
			"width": 150,
		},
	
		{
			"fieldname": "normal_rate",
			"fieldtype": "Data",
			"label": ("Hourly rate"),
			"width": 150,
		},
		{
			"fieldname": "type_of_ot",
			"label": "Type of OT",
			"fieldtype": "Data", 
			"width": 120
		},
		
		{
			"fieldname": "amount",
			"fieldtype": "Currency",
			"label": ("Amount"),
			"width": 150,
		},
		
	]


def get_data(filters):
	query ="""
		select ota.employee,ota.employee_name,ota.name,e.cost_center,otad.date,otad.from_date,otad.to_date,
		CASE
			WHEN otad.is_late_night_ot = 1 OR otad.is_holiday = 1 THEN otad.number_of_hours
			WHEN otad.is_late_night_ot = 0 AND otad.is_holiday = 0 THEN otad.number_of_hours
			ELSE 0
		END AS hours,
		CASE
			WHEN otad.is_late_night_ot = 1 OR otad.is_holiday = 1 THEN otad.rate
			WHEN otad.is_late_night_ot = 0 AND otad.is_holiday = 0 THEN otad.rate
			ELSE 0
		END AS number_rate,
		CASE 
			WHEN otad.is_late_night_ot = 1 OR otad.is_holiday = 1 THEN 'Special'
    		ELSE 'Normal'
		END AS type_of_ot,
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
