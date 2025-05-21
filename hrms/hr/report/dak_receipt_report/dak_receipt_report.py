# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	if not filters:
		filters = {}
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_conditions(filters=None):
	condition=""
	if filters.get("to_date"):
		condition+=" and date_of_receipt<='{}'".format(filters.get("to_date"))
	if filters.get("from_date"):
		condition+=" and date_of_receipt>='{}'".format(filters.get("from_date"))
	condition+=" order by date_of_receipt desc"
	return condition

def get_data(filters=None):
	if filters.get("to_date") or filters.get("from_date"):
		condition=get_conditions(filters)
		data=frappe.db.sql("select date_of_receipt, letter_no, from_whom_received, purpose, employee, employee_name,name from `tabDAK Receipt Register` where 1=1"+condition, as_dict=True)
	else:
		data=frappe.db.sql("select date_of_receipt, letter_no, from_whom_received, purpose, employee, employee_name,name from `tabDAK Receipt Register` where 1=1 order by date_of_receipt desc", as_dict=True)
	# frappe.throw(str(data))
	return data

# def get_conditions(filters=None):
	

def get_columns(filters=None):
	return [
		{
			"label": _("DAK Receipt ID"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "DAK Receipt Register",
			"width": 140,
		},
		{
			"label": _("Date of Receipt"),
			"fieldname": "date_of_receipt",
			"fieldtype": "Date",
			"width": 240,
		},
		{
			"label": _("Letter No"),
			"fieldname": "letter_no",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("From Whom Received"),
			"fieldname": "from_whom_received",
			"fieldtype": "Data",
			"width": 320,
		},
		{
			"label": _("Purpose"),
			"fieldname": "purpose",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Forward to Employee ID"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 220,
		},
		{
			"label": _("Forward to Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 220,
		},
		
	]
