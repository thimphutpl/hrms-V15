# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	if not filters:
		filters = {}
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_data(filters=None):
	if filters.get("to_date") or filters.get("from_date"):
		condition=get_conditions(filters)
		data=frappe.db.sql("select date, to_whom_sent, subject, file_no, place, remarks from `tabDispatch Register` where 1=1"+condition, as_dict=True)
	else:
		data=frappe.db.sql("select date, to_whom_sent, subject, file_no, place, remarks from `tabDispatch Register` where 1=1 order by date desc", as_dict=True)
	# frappe.throw(str(data))
	return data

def get_conditions(filters=None):
	condition=""
	if filters.get("to_date"):
		condition+=" and date<='{}'".format(filters.get("to_date"))
	if filters.get("from_date"):
		condition+=" and date>='{}'".format(filters.get("from_date"))
	condition+=" order by date desc"
	return condition
	
def get_columns(filters=None):
	return [
		{
			"label": _("Date"),
			"fieldname": "date",
			"fieldtype": "Date",
			"width": 140,
		},
		{
			"label": _("To Whom Sent"),
			"fieldname": "to_whom_sent",
			"fieldtype": "Data",
			"width": 180,
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
			"label": _("Name"),
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
