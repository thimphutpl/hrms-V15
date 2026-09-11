# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cstr


def execute(filters=None):
	if not filters:
		filters = {}

	data = []
	columns = []
	salary_structures = get_salary_structures(filters)
	if not salary_structures:
		return columns, data

	columns, earning_types, ded_types = get_columns(salary_structures)
	ss_earning_map = get_ss_earning_map(salary_structures)
	ss_ded_map = get_ss_ded_map(salary_structures)

	for ss in salary_structures:
		status = ""
		gross_pay = 0
		tot_ded = 0
		net_pay = 0
		if ss.is_active == "Yes":
			status = "Active"
		else:
			status = "Inactive"

		row = [ss.employee, ss.employee_name,
			   ss.bank_name, ss.bank_account_no,
			   ss.company, ss.branch, ss.department,
			   ss.division, ss.employee_grade,ss.employee_group, ss.designation,
			   status,
			   ss.from_date, ss.to_date]

		for e in earning_types:
			row.append(ss_earning_map.get(ss.name, {}).get(e))
			gross_pay += flt(ss_earning_map.get(ss.name, {}).get(e))

		gross_pay += flt(ss.arrear_amount) + flt(ss.leave_encashment_amount)

		row += [ss.arrear_amount, ss.leave_encashment_amount, gross_pay]

		for d in ded_types:
			row.append(ss_ded_map.get(ss.name, {}).get(d))
			tot_ded += flt(ss_ded_map.get(ss.name, {}).get(d))

		row += [tot_ded, gross_pay-tot_ded]

		data.append(row)

	return columns, data


def get_columns(salary_structures):
	columns = [
		_("Employee") + ":Link/Employee:80",
		_("Employee Name") + "::140",
		_("Bank Name") + "::80",
		_("Bank A/C#")+"::100",
		_("Company") + ":Link/Company:120",
		_("Branch") + ":Link/Branch:120",
		_("Department") + ":Link/Department:120",
		_("Division") + ":Link/Division:120",
		_("Grade") + ":Link/Employee Grade:120",
		_("Employee Group") + ":Link/Employee Group:120",
		_("Designation") + ":Link/Designation:120",
		_("Status") + "::100",
		_("From Date") + ":Date:80",
		_("To Date") + ":Date:80"
	]
	earning_types = []
	ded_types = []

	earning_types = frappe.db.sql_list("""select salary_component from `tabSalary Detail`
					where amount != 0 and parent in (%s)
					and parentfield = 'earnings'
					group by salary_component
					order by count(*) desc""" %
									   (', '.join(['%s']*len(salary_structures))), tuple([d.name for d in salary_structures]))

	ded_types = frappe.db.sql_list("""select salary_component from `tabSalary Detail`
					where amount != 0 and parent in (%s)
					and parentfield = 'deductions'
					group by salary_component
					order by count(*) desc""" %
								   (', '.join(['%s']*len(salary_structures))), tuple([d.name for d in salary_structures]))

	columns = columns + [(e + ":Currency:120") for e in earning_types] + \
		["Arrear Amount:Currency:120", "Leave Encashment Amount:Currency:150", "Gross Pay:Currency:120"] + \
		[(d + ":Currency:120") for d in ded_types] + \
		["Total Deduction:Currency:120", "Net Pay:Currency:120"]

	return columns, earning_types, ded_types


def get_salary_structures(filters):
	conditions, filters = get_conditions(filters)
	salary_structures = frappe.db.sql("""
				select t1.*, t2.bank_name, t2.bank_ac_no as bank_account_no
				from `tabSalary Structure` as t1, `tabEmployee` as t2
				where t2.name = t1.employee
				%s
				order by t1.employee""" % conditions, filters, as_dict=1)

	return salary_structures


def get_conditions(filters):
	conditions = ""
	status = {
		"All": "",
		"Active": "Yes",
		"Inactive": "No"
	}[filters.get("status")]

	if filters.get("company"):
		conditions += " and t1.company = %(company)s"
	if filters.get("employee"):
		conditions += " and t1.employee = %(employee)s"
	if filters.get("branch"):
		conditions += " and t1.branch = %(branch)s"
	if filters.get("grade"):
		conditions += " and t2.grade = %(grade)s"
	if filters.get("employee_group"):
		employee_groups = filters.get("employee_group")

		if isinstance(employee_groups, str):
			employee_groups = frappe.parse_json(employee_groups)

		conditions += " and t1.employee_group in %(employee_group)s"
		filters["employee_group"] = employee_groups

	if status:
		conditions += " and t1.is_active = '{0}'".format(status)
	

	return conditions, filters


# def get_ss_earning_map(salary_structures):
# 	ss_earning_map = {}

# 	ss_earnings = frappe.db.sql("""select parent, salary_component, sum(ifnull(amount,0)) as amount 
# 					from `tabSalary Detail` where parent in (%s)
# 					and parentfield = 'earnings'
# 					and ifnull(to_date, CURDATE()) >= DATE_ADD(LAST_DAY(DATE_SUB(CURDATE(), interval 30 day)), interval 1 day)
# 					group by parent, salary_component
# 					""" %
# 								(', '.join(['%s']*len(salary_structures))), tuple([d.name for d in salary_structures]), as_dict=1)

# 	for d in ss_earnings:
# 		ss_earning_map.setdefault(d.parent, frappe._dict()).setdefault(
# 			d.salary_component, [])
# 		ss_earning_map[d.parent][d.salary_component] = flt(d.amount)
# 	return ss_earning_map


# def get_ss_ded_map(salary_structures):
# 	ss_deductions = frappe.db.sql("""select parent, salary_component, sum(ifnull(amount,0)) as amount 
# 		from `tabSalary Detail` where parent in (%s)
# 		and parentfield = 'deductions'
# 		and ifnull(to_date, CURDATE()) >= DATE_ADD(LAST_DAY(DATE_SUB(CURDATE(), interval 30 day)), interval 1 day)
# 		group by parent, salary_component
# 		""" %
# 								  (', '.join(['%s']*len(salary_structures))), tuple([d.name for d in salary_structures]), as_dict=1)

# 	ss_ded_map = {}
# 	for d in ss_deductions:
# 		ss_ded_map.setdefault(d.parent, frappe._dict()
# 							  ).setdefault(d.salary_component, [])
# 		ss_ded_map[d.parent][d.salary_component] = flt(d.amount)

# 	return ss_ded_map


# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	if not filters:
		filters = {}

	data = []
	columns = []

	salary_structures = get_salary_structures(filters)

	if not salary_structures:
		return columns, data

	columns, earning_types, ded_types = get_columns(salary_structures)

	ss_earning_map = get_ss_earning_map(salary_structures)
	ss_ded_map = get_ss_ded_map(salary_structures)

	for ss in salary_structures:
		status = ""

		gross_pay = 0
		tot_ded = 0
		net_pay = 0

		if ss.is_active == "Yes":
			status = "Active"
		else:
			status = "Inactive"

		row = [
			ss.employee,
			ss.employee_name,
			ss.bank_name,
			ss.bank_account_no,
			ss.company,
			ss.branch,
			ss.department,
			ss.division,
			ss.employee_grade,
			ss.employee_group,
			ss.designation,
			status,
			ss.from_date,
			ss.to_date
		]

		# Earnings
		for e in earning_types:
			amount = flt(
				ss_earning_map.get(ss.name, {}).get(e, 0)
			)

			row.append(amount)
			gross_pay += amount

		# Arrear Amount and Leave Encashment Amount
		arrear_amount = flt(ss.arrear_amount)
		leave_encashment_amount = flt(ss.leave_encashment_amount)

		gross_pay += arrear_amount
		gross_pay += leave_encashment_amount

		row += [
			arrear_amount,
			leave_encashment_amount,
			gross_pay
		]

		# Deductions
		for d in ded_types:
			amount = flt(
				ss_ded_map.get(ss.name, {}).get(d, 0)
			)

			row.append(amount)
			tot_ded += amount

		# Total Deduction
		net_pay = gross_pay - tot_ded

		row += [
			tot_ded,
			net_pay
		]

		data.append(row)

	return columns, data


def get_columns(salary_structures):
	columns = [
		_("Employee") + ":Link/Employee:80",
		_("Employee Name") + "::140",
		_("Bank Name") + "::80",
		_("Bank A/C#") + "::100",
		_("Company") + ":Link/Company:120",
		_("Branch") + ":Link/Branch:120",
		_("Department") + ":Link/Department:120",
		_("Division") + ":Link/Division:120",
		_("Grade") + ":Link/Employee Grade:120",
		_("Employee Group") + ":Link/Employee Group:120",
		_("Designation") + ":Link/Designation:120",
		_("Status") + "::100",
		_("From Date") + ":Date:80",
		_("To Date") + ":Date:80"
	]

	earning_types = []
	ded_types = []

	if salary_structures:
		placeholders = ", ".join(["%s"] * len(salary_structures))
		names = tuple([d.name for d in salary_structures])

		# Get all Earnings.
		# No from_date/to_date filtering.
		earning_types = frappe.db.sql_list(
			"""
			SELECT salary_component
			FROM `tabSalary Detail`
			WHERE IFNULL(amount, 0) != 0
				AND parent IN (%s)
				AND parentfield = 'earnings'
			GROUP BY salary_component
			ORDER BY COUNT(*) DESC
			"""
			% placeholders,
			names
		)

		# Get all Deductions.
		# No from_date/to_date filtering.
		ded_types = frappe.db.sql_list(
			"""
			SELECT salary_component
			FROM `tabSalary Detail`
			WHERE IFNULL(amount, 0) != 0
				AND parent IN (%s)
				AND parentfield = 'deductions'
			GROUP BY salary_component
			ORDER BY COUNT(*) DESC
			"""
			% placeholders,
			names
		)

	columns = (
		columns
		+ [(e + ":Currency:120") for e in earning_types]
		+ [
			"Arrear Amount:Currency:120",
			"Leave Encashment Amount:Currency:150",
			"Gross Pay:Currency:120"
		]
		+ [(d + ":Currency:120") for d in ded_types]
		+ [
			"Total Deduction:Currency:120",
			"Net Pay:Currency:120"
		]
	)

	return columns, earning_types, ded_types


def get_salary_structures(filters):
	conditions, filters = get_conditions(filters)

	salary_structures = frappe.db.sql(
		"""
		SELECT
			t1.*,
			t2.bank_name,
			t2.bank_ac_no AS bank_account_no
		FROM `tabSalary Structure` AS t1
		INNER JOIN `tabEmployee` AS t2
			ON t2.name = t1.employee
		WHERE 1 = 1
			%s
		ORDER BY t1.employee
		"""
		% conditions,
		filters,
		as_dict=1
	)

	return salary_structures


def get_conditions(filters):
	conditions = ""

	status = {
		"All": "",
		"Active": "Yes",
		"Inactive": "No"
	}.get(filters.get("status"), "")

	if filters.get("company"):
		conditions += " AND t1.company = %(company)s"

	if filters.get("employee"):
		conditions += " AND t1.employee = %(employee)s"

	if filters.get("branch"):
		conditions += " AND t1.branch = %(branch)s"

	if filters.get("grade"):
		conditions += " AND t2.grade = %(grade)s"

	if filters.get("employee_group"):
		employee_groups = filters.get("employee_group")

		if isinstance(employee_groups, str):
			employee_groups = frappe.parse_json(employee_groups)

		conditions += " AND t1.employee_group IN %(employee_group)s"
		filters["employee_group"] = employee_groups

	if status:
		conditions += " AND t1.is_active = %(status)s"
		filters["status"] = status

	return conditions, filters


def get_ss_earning_map(salary_structures):
	ss_earning_map = {}

	if not salary_structures:
		return ss_earning_map

	placeholders = ", ".join(["%s"] * len(salary_structures))
	names = tuple([d.name for d in salary_structures])

	ss_earnings = frappe.db.sql(
		"""
		SELECT
			parent,
			salary_component,
			SUM(IFNULL(amount, 0)) AS amount
		FROM `tabSalary Detail`
		WHERE parent IN (%s)
			AND parentfield = 'earnings'
			AND IFNULL(amount, 0) != 0
		GROUP BY parent, salary_component
		"""
		% placeholders,
		names,
		as_dict=1
	)

	for d in ss_earnings:
		ss_earning_map.setdefault(d.parent, frappe._dict())
		ss_earning_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_earning_map


def get_ss_ded_map(salary_structures):
	ss_ded_map = {}

	if not salary_structures:
		return ss_ded_map

	placeholders = ", ".join(["%s"] * len(salary_structures))
	names = tuple([d.name for d in salary_structures])

	ss_deductions = frappe.db.sql(
		"""
		SELECT
			parent,
			salary_component,
			SUM(IFNULL(amount, 0)) AS amount
		FROM `tabSalary Detail`
		WHERE parent IN (%s)
			AND parentfield = 'deductions'
			AND IFNULL(amount, 0) != 0
		GROUP BY parent, salary_component
		"""
		% placeholders,
		names,
		as_dict=1
	)

	for d in ss_deductions:
		ss_ded_map.setdefault(d.parent, frappe._dict())
		ss_ded_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_ded_map
