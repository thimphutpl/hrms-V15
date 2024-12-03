# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_column(filters), get_data(filters)
	return columns, data


def get_data(filters=None):
	query = """
			select
		
			pbva_table.employee,
			pbva_table.employee_name,
			pbva_table.grade,
			pbva_table.date_of_joining,
			pbva_table.cost_center,
			pbva_table.total_basic_pay,
			pbva_table.days_worked,
			pbva_table.pbva_percent,
			pbva_table.amount,
			pbva_table.total_rating,
			pbva_table.unit_rating,
			pbva_table.employee_rating,
			ee.designation
		
			from 
				`tabPBVA Details` pbva_table 
			join
				`tabPBVA` pbva 
			on  pbva_table.parent = pbva.name

			join 
				`tabEmployee` ee
			on  pbva_table.employee=ee.name
		
			where 
				1=1 
		"""
	if filters.branch:
		query += " and pbva_table.branchs= '{}'".format(filters.branch)
	if filters.fiscal_year:
		query += " and pbva.fiscal_year='{}'".format(filters.fiscal_year)

		
	return frappe.db.sql(query, as_dict=True)
	  

	
	

def get_column(filters=None):
	return [
		{
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": _("Employee"),
			"options": "Employee",
			"width": 150,
		},
		{
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"label": _("Employee Name"),
			"width": 150,
		},
		{
			"fieldname": "designation",
			"fieldtype": "Link",
			"label": _("Designation"),
			"options": "Designation",
			"width": 150,
		},
		{
			"fieldname": "grade",
			"fieldtype": "Link",
			"label": _("Grade"),
			"options": "Employee Grade",
			"width": 150,
		},
		{
			"fieldname": "cost_center",
			"fieldtype": "Link",
			"label": _("Cost Center"),
			"options": "Cost Center",
			"width": 150,
		},
		{
			"fieldname": "date_of_joining",
			"fieldtype": "Date",
			"label": _("Date of Joining"),
			"width": 150,
		},
		{
			"fieldname": "total_basic_pay",
			"fieldtype": "Data",
			"label": _("Total Basic Pay"),
			"width": 150,
		},
		{
			"fieldname": "days_worked",
			"fieldtype": "Data",
			"label": _("No. Days Served"),
			"width": 150,
		},
		{
			"fieldname": "employee_rating",
			"fieldtype": "Data",
			"label": _("Employee Rating"),
			"width": 150,
		},
		{
			"fieldname": "unit_rating",
			"fieldtype": "Data",
			"label": _("Unit Rating"),
			"width": 150,
		},
		{
			"fieldname": "total_rating",
			"fieldtype": "Data",
			"label": _("New Rating"),
			"width": 150,
		},
		{
			"fieldname": "pbva_percent",
			"fieldtype": "Data",
			"label": _("PBVA Percent"),
			"width": 150,
		},
		{
			"fieldname": "amount",
			"fieldtype": "Data",
			"label": _("PBVA Amount"),
			"width": 150,
		}
		
	]
