# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_data(filters=None):
    data=frappe.db.sql("select date, company, department, subject, file_no, place, remarks from `tabDispatch Register` where 1=1", as_dict=True)
    # frappe.throw(str(data))
    return data

# def get_conditions(filters=None):
    

def get_columns(filters=None):
    return [
		{
			"label": _("Date"),
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 140,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 180,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options":"Department",
			"width": 240,
		},
		{
			"label": _("Subject"),
			"fieldname": "subject",
			"fieldtype": "Data",
			"width": 320,
		},
		{
			"label": _("File No"),
			"fieldname": "file_no",
			"fieldtype": "Data",
			"width": 140,
		},
		{
			"label": _("Place"),
			"fieldname": "place",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("Remarks"),
			"fieldname": "remarks",
			"fieldtype": "Data",
			"width": 220,
		},
		
	]
