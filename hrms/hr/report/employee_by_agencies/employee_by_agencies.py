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
    cond = get_condition(filters)
    current_user = frappe.session.user
    user_roles = frappe.get_roles(current_user)
    if "Dashboard Manager Overall" or "System Manager" in user_roles:
        return frappe.db.sql("""
		select company,count(name) from `tabEmployee` group by company {condition}
		""".format(condition=cond))
    else:
        company = frappe.db.sql('''
                                select company from `tabEmployee` where user_id="{}"
                                '''.format(current_user), as_dict=True)
        if company:
            
            return frappe.db.sql("""
            select company,count(name) from `tabEmployee` where company ="{condition}" group by company
            """.format(condition=company[0]['company']))
    
    
def get_condition(filters):
    conds = ""
    if filters.company:
        conds += "and company='{}'".format(filters.category)
    return conds
