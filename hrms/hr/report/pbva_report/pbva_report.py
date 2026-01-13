# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# added by kinzang. n
def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
         {"fieldname": "name", "label": "PBVA ID", "fieldtype": "Link", "options": "PBVA", "width": 150},
        {"fieldname": "employee", "fieldtype": "Link", "label": _("Employee"), "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "fieldtype": "Data", "label": _("Employee Name"), "width": 150},
        {"fieldname": "branch", "fieldtype": "Data", "label": _("Branch"), "width": 150},
        
        {"fieldname": "grade", "fieldtype": "Link", "label": _("Grade"), "options": "Employee Grade", "width": 150},
        {"fieldname": "cost_center", "fieldtype": "Link", "label": _("Cost Center"), "options": "Cost Center", "width": 150},
        {"fieldname": "date_of_joining", "fieldtype": "Date", "label": _("Date of Joining"), "width": 150},
        {"fieldname": "days_worked", "fieldtype": "Data", "label": _("No. Days Served"), "width": 150},
        {"fieldname": "total_basic_pay", "fieldtype": "Data", "label": _("Basic Pay"), "width": 150},
         {"fieldname": "amount", "fieldtype": "Data", "label": _("Total PBVA Amount"), "width": 150},
		  {"fieldname": "tax_amount", "fieldtype": "Data", "label": _("Tax Amount"), "width": 150},
        {"fieldname": "balance_amount", "fieldtype": "Data", "label": _("Net PBVA Amount"), "width": 150},
        
        
        {"fieldname": "employee_rating", "fieldtype": "Data", "label": _("Employee Rating"), "width": 150},
        {"fieldname": "unit_rating", "fieldtype": "Data", "label": _("Unit Rating"), "width": 150},
        {"fieldname": "total_rating", "fieldtype": "Data", "label": _("New Rating"), "width": 150},
        {"fieldname": "pbva_percent", "fieldtype": "Data", "label": _("PBVA Percent"), "width": 150},
         {"fieldname": "tpn_number", "label": "TPN Number", "fieldtype": "Link", "options": "Employee", "width": 150},
        
    ]

def get_data(filters):
    filters = filters or {}
    conditions = []
    values = {}

    # Filters
    if filters.get("employee"):
        conditions.append("pbva_table.employee = %(employee)s")
        values["employee"] = filters["employee"]

    if filters.get("fiscal_year"):
        conditions.append("pbva.fiscal_year = %(fiscal_year)s")
        values["fiscal_year"] = filters["fiscal_year"]

    if filters.get("branch"):
        conditions.append("pbva_table.branch = %(branch)s")
        values["branch"] = filters["branch"]

    if filters.get("company"):
        conditions.append("pbva_table.company = %(company)s")
        values["company"] = filters["company"]

    condition_sql = " AND ".join(conditions)
    if condition_sql:
        condition_sql = " AND " + condition_sql

    query = f"""
        SELECT
            pbva.name,
            pbva_table.employee,
            pbva_table.employee_name,
            pbva_table.branch,
            pbva_table.grade,
            pbva_table.date_of_joining,
            pbva_table.cost_center,
            pbva_table.days_worked,
            pbva_table.total_basic_pay,
            pbva_table.amount,
            pbva_table.tax_amount,
            pbva_table.balance_amount,
            pbva_table.employee_rating,
            pbva_table.unit_rating,
            pbva_table.total_rating,
            pbva_table.pbva_percent,
            emp.tpn_number
        FROM `tabPBVA` pbva
        INNER JOIN `tabPBVA Details` pbva_table
            ON pbva_table.parent = pbva.name
        INNER JOIN `tabEmployee` emp
            ON emp.name = pbva_table.employee
        WHERE pbva.docstatus = 1
        {condition_sql}
    """

    data = frappe.db.sql(query, values, as_dict=True)

    # ---------------------------
    # 🔹 Calculate Totals
    # ---------------------------
    total_basic_pay = 0
    total_tax = 0
    total_amount = 0

    for row in data:
        total_basic_pay += row.get("total_basic_pay") or 0
        total_tax += row.get("tax_amount") or 0
        total_amount += row.get("amount") or 0

    # ---------------------------
    # 🔹 Append Total Row
    # ---------------------------
    data.append({
        "employee": "Total",  # plain text
        "employee_name": "",
        "branch": "",
        "total_basic_pay": total_basic_pay,
        "tax_amount": total_tax,
        "amount": total_amount
    })

    return data


	#till here


# def get_data(filters=None):
# 	query = """
# 			select
		
# 			pbva_table.employee,
# 			pbva_table.employee_name,
# 			pbva_table.grade,
# 			pbva_table.date_of_joining,
# 			pbva_table.cost_center,
# 			pbva_table.total_basic_pay,
# 			pbva_table.days_worked,
# 			pbva_table.pbva_percent,
# 			pbva_table.amount,
# 			pbva_table.total_rating,
# 			pbva_table.unit_rating,
# 			pbva_table.employee_rating,
# 			ee.designation
		
# 			from 
# 				`tabPBVA Details` pbva_table 
# 			join
# 				`tabPBVA` pbva 
# 			on  pbva_table.parent = pbva.name

# 			join 
# 				`tabEmployee` ee
# 			on  pbva_table.employee=ee.name
		
# 			where 
# 				1=1 
# 		"""
# 	if filters.branch:
# 		query += " and pbva_table.branchs= '{}'".format(filters.branch)
# 	if filters.fiscal_year:
# 		query += " and pbva.fiscal_year='{}'".format(filters.fiscal_year)

		
# 	return frappe.db.sql(query, as_dict=True)
	  

	
	

# def get_column(filters=None):
# 	return [
# 		{
# 			"fieldname": "employee",
# 			"fieldtype": "Link",
# 			"label": _("Employee"),
# 			"options": "Employee",
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "employee_name",
# 			"fieldtype": "Data",
# 			"label": _("Employee Name"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "designation",
# 			"fieldtype": "Link",
# 			"label": _("Designation"),
# 			"options": "Designation",
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "grade",
# 			"fieldtype": "Link",
# 			"label": _("Grade"),
# 			"options": "Employee Grade",
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "cost_center",
# 			"fieldtype": "Link",
# 			"label": _("Cost Center"),
# 			"options": "Cost Center",
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "date_of_joining",
# 			"fieldtype": "Date",
# 			"label": _("Date of Joining"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "total_basic_pay",
# 			"fieldtype": "Data",
# 			"label": _("Total Basic Pay"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "days_worked",
# 			"fieldtype": "Data",
# 			"label": _("No. Days Served"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "employee_rating",
# 			"fieldtype": "Data",
# 			"label": _("Employee Rating"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "unit_rating",
# 			"fieldtype": "Data",
# 			"label": _("Unit Rating"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "total_rating",
# 			"fieldtype": "Data",
# 			"label": _("New Rating"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "pbva_percent",
# 			"fieldtype": "Data",
# 			"label": _("PBVA Percent"),
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "amount",
# 			"fieldtype": "Data",
# 			"label": _("PBVA Amount"),
# 			"width": 150,
# 		}
		
# 	]
