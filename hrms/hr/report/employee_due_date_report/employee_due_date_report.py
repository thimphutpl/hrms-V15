# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
import frappe

def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	#filters = get_filters(filters)

	return columns, data

def get_columns(filters):
	cols = [
		("Employee No.") + ":data:150",
		("Employee Name") + ":data:150",
		("Branch")+":data:150",
		("Department")+":data:150",
		("Division")+":data:150",
	]
	if filters.uinput == "promotion_due_date":
		cols.append(("Promotion Due Date")+":date:170")
	if filters.uinput == "contract_end_date":
		cols.append(("Contract End Date")+":date:170")
	if filters.uinput == "date_of_retirement":
		cols.append(("Date of Retirement")+":date:170")
	return cols

def get_data(filters):
	data = "select name, employee_name, branch, department,division, " + str(filters.uinput) +" FROM `tabEmployee` where status = 'Active' and " + str(filters.uinput) + " is not null"
	if filters.get("branch"):
		data += " and branch = \'" + str(filters.branch) + "\'"
	if filters.get("from_date") and filters.get("to_date"):
		data += " and " + str(filters.uinput) +" between \'" + str(filters.from_date) + "\' and \'"+ str(filters.to_date) + "\'"
	return frappe.db.sql(data)
