# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
		columns = get_columns()
		data = get_data(filters)

		return columns, data
	
def get_columns():
		return [
				("Name ") + ":Link/Salary Increment:200",
		("Branch ") + ":Link/Equipment:200",
				("Employee ID") + ":Link/Employee:100",
				("Employee Name") + ":Data:150",
		("Year") + ":Data:80",
				("Month")+ ":Data:50",
				("Current Basic") + ":Currency:120",
				("Increment") + ":Currency:80",
				("New Basic") + ":Currency:120"
		]


def get_data(filters):
    query = """SELECT 
                   name, 
                   branch, 
                   employee, 
                   employee_name, 
                   fiscal_year, 
                   month, 
                   old_basic, 
                   increment, 
                   (COALESCE(old_basic, 0) + COALESCE(increment, 0)) AS new_basic
               FROM `tabSalary Increment` 
               WHERE 1=1
            """
    
    if filters.get("uinput"):
        if filters.uinput == "Draft":
            query += " AND docstatus = 0"
        elif filters.uinput == "Submitted":
            query += " AND docstatus = 1"

    if filters.get("branch"):
        query += " AND branch = '{}'".format(filters.branch)
    if filters.get("fiscal_year"):
        query += " AND fiscal_year = '{}'".format(filters.fiscal_year)
    if filters.get("month"):
        query += " AND month = '{}'".format(filters.get("month"))

    query += " ORDER BY branch"

    # Debug the query
    frappe.throw(str(query))  

    return frappe.db.sql(query, as_dict=1, debug=1)
		
# def get_data(filters):

# 	query =  """select name, branch, employee, employee_name, fiscal_year, month, old_basic, 
# 				increment, new_basic 
# 				from `tabSalary Increment` 
# 				where 1=1
# 			"""
# 	frappe.throw(str(query))		
# 	if filters.uinput == "Draft":
# 		query += " and docstatus = 0"
# 	if filters.uinput == "Submitted":
# 		query += " and docstatus = 1"
# 	if filters.get("branch"):
# 		query += " and branch = '{}'".format(filters.branch)
# 	if filters.get("fiscal_year"):
# 		query += " and fiscal_year = '{}'".format(filters.fiscal_year)

# 	if filters.get("month"):
#     	query += " and month = '{}' ".format(filters.get("month"))
#     # frappe.msgprint(docstatus)  # Uncomment if needed for debugging
# 	query += " order by branch"

# 	# if filters.get("month") and filters.get("month") == 'January':
# 	# 	query += " and month = '{}' ".format(filters.month)
# 	# if filters.get("month") and filters.get("month") == 'July':
# 	# 	query += " and month = '{}' ".format(filters.month)
# 	# 	#frappe.msgprint(docstatus)
# 	# 	query += " order by branch"
# 	return frappe.db.sql(query, debug =1)
	  
