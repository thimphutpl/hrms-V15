# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = get_column(), get_data(filters)
	return columns, data

def get_column():
    columns = [
		("Agency") + ":Link/eNote:100",
		("Total Number") + ":Data:200",
    ]
    return columns

def get_data(filters):
    cond = get_conditions(filters)
    return frappe.db.sql("""
        SELECT company, COUNT(name) 
        FROM `tabEmployee` 
        WHERE 1=1 {condition} 
        GROUP BY company
    """.format(condition=cond))
    

  
def get_conditions(filters):
	conditions = []
	if filters and filters.get("department"):
		conditions.append("department = '{}'".format(filters.get("department")))
	return "AND {}".format(" AND ".join(conditions)) if conditions else ""
