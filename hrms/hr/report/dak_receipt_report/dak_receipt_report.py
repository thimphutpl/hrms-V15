# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_data(filters=None):
    data=frappe.db.sql("select date_of_receipt, letter_no, postage, from_whom_received, purpose, employee, employee_name from `tabDAK Receipt Register` where 1=1", as_dict=True)
    # frappe.throw(str(data))
    return data

# def get_conditions(filters=None):
    

def get_columns(filters=None):
    return [
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
			"label": _("Postage"),
			"fieldname": "postage",
			"fieldtype": "Data",
			"width": 240,
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
