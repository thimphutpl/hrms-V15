# # Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt

# import frappe
# from frappe import _


# def execute(filters=None):
# 	if not filters:
# 		filters = {}
# 	columns, data = [], []
# 	data = get_data(filters)
# 	if not data:
# 		return columns, data
# 	columns = get_columns(data)
# 	return columns, data

# def get_columns(data):
# 	columns = [
# 		_("Employee") + ":Link/Employee:80", 
# 		_("Employee Name") + ":Data:140", 
# 		_("Employee Group")+":Data:140",
# 		_("CID") + ":Data:120", 
# 		_("Designation") + ":Link/Designation:120",
# 		_("Loan Type") + ":Data:140", 
# 		_("Loan From") + ":Data:160", 
# 		_("Account No") + ":Data:140",  
# 		_("Deduction Amount") + ":Currency:140", 
# 		_("Total Deductible Amount") + ":Currency:170", 
# 		_("Balance Amount") + ":Currency:140",
# 		_("Company") + ":Link/Company:120", 
# 		_("Cost Center") + ":Link/Cost Center:120", 
# 		_("Branch") + ":Link/Branch:120", 
# 		_("Department") + ":Link/Department:120",
# 		_("Division") + ":Link/Department:120", 
# 		_("Section") + ":Link/Department:120", 
# 		_("Year") + ":Data:80", 
# 		_("Month") + ":Data:80"
# 	]
# 	return columns

# def get_data(filters):
# 	conditions, filters = get_conditions(filters)

# 	data = frappe.db.sql("""
# 		select t1.employee, t3.employee_name,t1.employee_group, t3.passport_number, t1.designation,
# 			t2.reference_type, t2.institution_name, t2.reference_number, t2.amount, t2.total_deductible_amount, t2.total_outstanding_amount,
# 			t1.company, t1.cost_center, t1.branch, t1.department, t1.division, t1.section,
# 			t1.fiscal_year, t1.month
# 		from `tabSalary Slip` t1, `tabSalary Detail` t2, `tabEmployee` t3
# 		where t1.docstatus = 1 {}
# 		and t3.employee = t1.employee
# 		and t2.parent = t1.name
# 		and t2.parentfield = 'deductions'
# 		and case when t2.institution_name = 'RICBL' then t2.reference_type like '%loan%' else 1 = 1 end
# 		and exists
# 			(select 1
# 				from `tabSalary Component` sc
# 				where sc.name = t2.salary_component
# 			)
# 	""".format(conditions))
# 	return data

# def get_conditions(filters):
# 	conditions = ""
# 	if filters.get("month"):
# 		month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", 
# 			"Dec"].index(filters["month"]) + 1
# 		filters["month"] = month
# 		conditions += " and t1.month = {}".format(filters.get("month"))
	
# 	if filters.get("fiscal_year"): conditions += " and t1.fiscal_year = {}".format(filters.get("fiscal_year"))
# 	if filters.get("company"): conditions += " and t1.company = '{}'".format(filters.get("company"))
# 	if filters.get("employee"): conditions += " and t1.employee = '{}'".format(filters.get("employee"))
# 	if filters.get("bank"): conditions += "and t2.institution_name = '{0}'".format(filters.bank)
# 	if filters.get("cost_center"): conditions += " and exists(select 1 from `tabCost Center` cc where t1.cost_center = cc.name and (cc.parent_cost_center = '{0}' or cc.name = '{0}'))".format(filters.cost_center)
# 	if filters.get("employee_group"):
# 		employee_groups = filters.get("employee_group")

# 		if isinstance(employee_groups, str):
# 			employee_groups = frappe.parse_json(employee_groups)

# 		if employee_groups:
# 			conditions += """
# 				AND t1.employee_group IN %(employee_group)s
# 			"""

# 			filters["employee_group"] = employee_groups

# 	return conditions, filters

# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns, data = [], []
	data = get_data(filters)

	if not data:
		return columns, data

	columns = get_columns(data)

	return columns, data


def get_columns(data):
	return [
		{
			"fieldname":"company",
			"label": _("Company"),
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"fieldname": "fiscal_year",
			"label": _("Year"),
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"fieldname": "month",
			"label": _("Month"),
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 100,
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "employee_group",
			"label": _("Employee Group"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "cid",
			"label": _("CID"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "designation",
			"label": _("Designation"),
			"fieldtype": "Link",
			"options": "Designation",
			"width": 140,
		},
		{
			"fieldname": "loan_type",
			"label": _("Loan Type"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "loan_from",
			"label": _("Loan From"),
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"fieldname": "account_no",
			"label": _("Account No"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "deduction_amount",
			"label": _("Deduction Amount"),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "total_deductible_amount",
			"label": _("Total Deductible Amount"),
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"fieldname": "balance_amount",
			"label": _("Balance Amount"),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "cost_center",
			"label": _("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center",
			"width": 150,
		},
		{
			"fieldname": "branch",
			"label": _("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": 130,
		},
		{
			"fieldname": "department",
			"label": _("Department"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"fieldname": "division",
			"label": _("Division"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		{
			"fieldname": "section",
			"label": _("Section"),
			"fieldtype": "Link",
			"options": "Department",
			"width": 150,
		},
		
	]




def get_data(filters):
	conditions, values = get_conditions(filters)

	values["financial_loan_pattern"] = "Financial Institution Loan%"
	# values["ricbl_institution"] = "RICBL"

	data = frappe.db.sql("""
		SELECT
		    t1.company as company,
			t1.fiscal_year as  fiscal_year,
			t1.month as month,
			t1.employee,
			t3.employee_name,
			t1.employee_group,
			t3.passport_number,
			t1.designation,
			t2.salary_component,
			t2.institution_name as loan_from,
			t2.reference_number as account_no,		
			t2.amount,
			t2.total_deductible_amount,
			t2.total_outstanding_amount,
			t1.cost_center,
			t1.branch,
			t1.department,
			t1.division,
			t1.section

		

		FROM `tabSalary Slip` t1
		INNER JOIN `tabSalary Detail` t2
			ON t2.parent = t1.name
			AND t2.parentfield = 'deductions'

		INNER JOIN `tabEmployee` t3
			ON t3.employee = t1.employee

		WHERE t1.docstatus = 1
		{}

	
		AND (
	(
		t2.salary_component LIKE %(financial_loan_pattern)s
	)
)
		

		AND EXISTS (
			SELECT 1
			FROM `tabSalary Component` sc
			WHERE sc.name = t2.salary_component
		)

		ORDER BY
			t1.employee,
			t2.institution_name

	""".format(conditions), values)


	return data


def get_conditions(filters):
	conditions = ""
	values = {}

	# Month
	if filters.get("month"):
		month = [
			"Jan", "Feb", "Mar", "Apr",
			"May", "Jun", "Jul", "Aug",
			"Sep", "Oct", "Nov", "Dec"
		].index(filters["month"]) + 1

		conditions += " and t1.month = %(month)s"
		values["month"] = month

	# Fiscal Year
	if filters.get("fiscal_year"):
		conditions += " and t1.fiscal_year = %(fiscal_year)s"
	values["fiscal_year"] = filters.get("fiscal_year")

	# Company
	if filters.get("company"):
		conditions += " and t1.company = %(company)s"
		values["company"] = filters.get("company")

	# Employee
	if filters.get("employee"):
		conditions += " and t1.employee = %(employee)s"
		values["employee"] = filters.get("employee")

	# Bank
	if filters.get("bank"):
		conditions += " and t2.institution_name = %(bank)s"
		values["bank"] = filters.get("bank")
        

	# Employee Group
	if filters.get("employee_group"):
		employee_groups = filters.get("employee_group")

		if isinstance(employee_groups, str):
			employee_groups = frappe.parse_json(employee_groups)

		if employee_groups:
			conditions += """
				AND t1.employee_group IN %(employee_group)s
			"""

			values["employee_group"] = tuple(employee_groups)

	# Cost Center
	if filters.get("cost_center"):
		conditions += """
			AND EXISTS (
				SELECT 1
				FROM `tabCost Center` cc
				WHERE t1.cost_center = cc.name
				AND (
					cc.parent_cost_center = %(cost_center)s
					OR cc.name = %(cost_center)s
				)
			)
		"""

		values["cost_center"] = filters.get("cost_center")

	return conditions, values
