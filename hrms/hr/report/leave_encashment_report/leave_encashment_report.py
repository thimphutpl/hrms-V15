# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

#added by kinzang. N to get Bulk leave enchashment report with TPN number

def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "name", "label": "Leave Encashment ID", "fieldtype": "Link", "options": "Bulk Leave Encashment", "width": 150},
         {"fieldname": "fiscal_year", "label": "Year", "fieldtype": "Data", "width": 150},
        {"fieldname": "encashment_date", "label": "Encashment Date", "fieldtype": "Date", "width": 150},
        {"fieldname": "leave_type", "label": "Leave Type", "fieldtype": "Link", "options": "Leave Type", "width": 150},
        {"fieldname": "employee", "label": "Employee", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "designation", "label": "Designation", "fieldtype": "Data", "width": 150},
        {"fieldname": "leave_balance", "label": "Leave Balance", "fieldtype": "Data", "width": 150},
        {"fieldname": "encashable_days", "label": "Encashable Days", "fieldtype": "Data", "width": 150},
        {"fieldname": "current_basic_pay", "label": "Basic Pay", "fieldtype": "Currency", "width": 150},
        {"fieldname": "encashment_amount", "label": "Encashment Amount", "fieldtype": "Currency", "width": 150},
        {"fieldname": "encashment_tax", "label": "Encashment Tax", "fieldtype": "Currency", "width": 150},
        {"fieldname": "payable_amount", "label": "Net Amount", "fieldtype": "Currency", "width": 150},
        {"fieldname": "branch", "label": "Branch", "fieldtype": "Link", "options": "Branch", "width": 150},
        {"fieldname": "tpn_number", "label": "TPN Number", "fieldtype": "Link", "options": "Employee", "width": 150},
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters.get("employee"):
        conditions.append("lei.employee = %(employee)s")
        values["employee"] = filters["employee"]

    if filters.get("fiscal_year"):
        conditions.append("le.fiscal_year = %(fiscal_year)s")
        values["fiscal_year"] = filters["fiscal_year"]  

    if filters.get("branch"):
        conditions.append("lei.branch = %(branch)s")
        values["branch"] = filters["branch"]         

    if filters.get("company"):
        conditions.append("lei.company = %(company)s")
        values["company"] = filters["company"]

    condition_sql = " AND ".join(conditions)
    if condition_sql:
        condition_sql = " AND " + condition_sql

    query = f"""
        SELECT
            le.name,
            le.fiscal_year,

            le.encashment_date,
            le.leave_type,
            lei.employee,
            lei.employee_name,
            lei.designation,
            lei.leave_balance,
            lei.encashable_days,
            lei.current_basic_pay,
            lei.encashment_amount,
            lei.encashment_tax,
            lei.payable_amount,
            lei.branch,
            emp.tpn_number
        FROM `tabBulk Leave Encashment` le
        INNER JOIN `tabBulk Leave Encashment Item` lei
            ON lei.parent = le.name
        INNER JOIN `tabEmployee` emp
			ON emp.name = lei.employee
        
        WHERE le.docstatus = 1
        {condition_sql}
    """

    return frappe.db.sql(query, values, as_dict=True)
# till here.


# def get_data(filters=None):
# 	query = """
# 		SELECT
# 		le.name,
# 		le.employee,
# 		le.employee_name,
# 		le.designation,
# 		le.division,
# 		le.encashment_date,
# 		le.leave_type,
# 		le.basic_pay,
# 		le.branch,
# 		le.cost_center
# 		FROM 
# 			`tabLeave Encashment` AS le
# 		WHERE 
# 			le.docstatus = 0
# 		"""
# 	if filters.get("employee"):
# 		query += " and le.employee = \'" + str(filters.employee)+ "\'"	

# 	if filters.get("company"):
# 		query += " and le.company = \'" + str(filters.company) + "\'"		
# 	return  frappe.db.sql(query)
