# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe

# Copyright (c) 2026
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import date
from calendar import monthrange


MONTH_MAP = {
	"Jan": 1,
	"Feb": 2,
	"Mar": 3,
	"Apr": 4,
	"May": 5,
	"Jun": 6,
	"Jul": 7,
	"Aug": 8,
	"Sep": 9,
	"Oct": 10,
	"Nov": 11,
	"Dec": 12,
}


# These are the employment types that should appear under:
# Musterroll/OAP/Operator/GFG/DFG
PAYABLE_EMPLOYMENT_TYPES = [
	"Muster Roll Employee",
	"Open Air Prisoner",
	"Operator",
	"GFG",
	"DFG",
]


# Update this list only if your OT Salary Component name is different.
# The report will calculate:
# Payable Gross Pay = Salary Slip Gross Pay
# Payable OT Amount = matching OT component amount
# Payable Total Wage = Gross Pay - OT Amount
OT_SALARY_COMPONENTS = [
	"Total OT",
	"OT",
	"OT Amount",
	"Overtime",
	"Over Time",
]


# def execute(filters=None):
# 	filters = frappe._dict(filters or {})
# 	validate_filters(filters)

# 	columns = get_columns()
# 	data = []

# 	show_detail = flt(filters.get("show_detail"))

# 	# 1. Normal salary slipped employees
# 	salary_rows = get_salary_slip_summary(filters)
# 	if salary_rows:
# 		data.extend(salary_rows)
# 		data.append(get_section_total_row("Sub Total - Salary Slipped Employees", salary_rows))

# 		if show_detail:
# 			detail_rows = get_salary_slip_detail(filters)
# 			if detail_rows:
# 				data.extend(detail_rows)

# 	# 2. Muster Roll / OAP / Operator / GFG / DFG
# 	payable_rows = get_salary_payable_summary(filters)
# 	if payable_rows:
# 		data.extend(payable_rows)
# 		data.append(get_section_total_row("Sub Total - Musterroll/OAP/Operator/GFG/DFG", payable_rows))

# 		if show_detail:
# 			payable_detail_rows = get_salary_payable_detail(filters)
# 			if payable_detail_rows:
# 				data.extend(payable_detail_rows)

# 	# 3. Consultant payment through Journal Entry
# 	consultant_rows = get_consultant_je_summary(filters)
# 	if consultant_rows:
# 		data.extend(consultant_rows)
# 		data.append(get_section_total_row("Sub Total - Consultant JE", consultant_rows))

# 	# 4. Grand Total
# 	if data:
# 		data.append(get_grand_total_row(data))

# 	return columns, data

def execute(filters=None):
	filters = frappe._dict(filters or {})
	validate_filters(filters)

	columns = get_columns()
	data = []

	show_detail = flt(filters.get("show_detail"))
	only_slipped_employees = flt(filters.get("only_slipped_employees"))
	only_others = flt(filters.get("only_others"))

	if only_slipped_employees and only_others:
		frappe.throw(_("Please select either Only Slipped Employees or Only Others, not both."))

	show_slipped = True
	show_others = True

	if only_slipped_employees:
		show_others = False

	if only_others:
		show_slipped = False

	# 1. Salary slipped employees
	if show_slipped:
		salary_rows = get_salary_slip_summary(filters)
		if salary_rows:
			data.extend(salary_rows)
			data.append(get_section_total_row("Sub Total - Salary Slipped Employees", salary_rows))

			if show_detail:
				detail_rows = get_salary_slip_detail(filters)
				if detail_rows:
					data.extend(detail_rows)

	# 2. Others from MR Payment
	if show_others:
		payable_rows = get_salary_payable_summary(filters)
		if payable_rows:
			data.extend(payable_rows)
			data.append(get_section_total_row("Sub Total - Musterroll/OAP/Operator/GFG/DFG", payable_rows))

			if show_detail:
				payable_detail_rows = get_salary_payable_detail(filters)
				if payable_detail_rows:
					data.extend(payable_detail_rows)

		# 3. Consultant JE, only if consultant account selected
		consultant_rows = get_consultant_je_summary(filters)
		if consultant_rows:
			data.extend(consultant_rows)
			data.append(get_section_total_row("Sub Total - Consultant JE", consultant_rows))

	# 4. Grand Total
	if data:
		data.append(get_grand_total_row(data))

	return columns, data


def validate_filters(filters):
	if not filters.get("company"):
		frappe.throw(_("Company is required"))

	if not filters.get("fiscal_year"):
		frappe.throw(_("Fiscal Year is required"))

	if not filters.get("month"):
		frappe.throw(_("Month is required"))

	if filters.month not in MONTH_MAP:
		frappe.throw(_("Invalid month selected"))


def get_columns():
	return [
		{
			"label": _("Section"),
			"fieldname": "section",
			"fieldtype": "Data",
			"width": 260,
		},
		{
			"label": _("Branch / Cost Center"),
			"fieldname": "branch",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Employment Type / Category"),
			"fieldname": "category",
			"fieldtype": "Data",
			"width": 220,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 130,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Employee Count"),
			"fieldname": "employee_count",
			"fieldtype": "Int",
			"width": 120,
		},
		{
			"label": _("Net Pay"),
			"fieldname": "net_pay",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Total Wage"),
			"fieldname": "total_wage",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Total OT"),
			"fieldname": "ot_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Gross Pay"),
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Consultant Paid"),
			"fieldname": "consultant_paid",
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 150,
		},
	]


def get_period(filters):
	month_no = MONTH_MAP[filters.month]

	fiscal_year = frappe.db.get_value(
		"Fiscal Year",
		filters.fiscal_year,
		["year_start_date", "year_end_date"],
		as_dict=True,
	)

	if not fiscal_year:
		frappe.throw(_("Fiscal Year {0} not found").format(filters.fiscal_year))

	fy_start = getdate(fiscal_year.year_start_date)
	fy_end = getdate(fiscal_year.year_end_date)

	for year in range(fy_start.year, fy_end.year + 1):
		month_start = date(year, month_no, 1)
		month_end = date(year, month_no, monthrange(year, month_no)[1])

		if month_start <= fy_end and month_end >= fy_start:
			return month_start, month_end

	frappe.throw(_("Selected month does not fall inside the selected Fiscal Year"))


def has_column(doctype, fieldname):
	return frappe.db.has_column(doctype, fieldname)


def get_branch_expr(employee_alias="emp", salary_slip_alias="ss"):
	if has_column("Salary Slip", "branch"):
		return f"COALESCE({salary_slip_alias}.branch, {employee_alias}.branch, 'No Branch')"

	return f"COALESCE({employee_alias}.branch, 'No Branch')"


def get_common_salary_conditions(filters, values, employee_alias="emp", salary_slip_alias="ss"):
	from_date, to_date = get_period(filters)

	conditions = [
		f"{salary_slip_alias}.docstatus = 1",
		f"{salary_slip_alias}.company = %(company)s",
		f"{salary_slip_alias}.start_date <= %(to_date)s",
		f"{salary_slip_alias}.end_date >= %(from_date)s",
	]

	values.update({
		"company": filters.company,
		"from_date": from_date,
		"to_date": to_date,
	})

	branch_expr = get_branch_expr(employee_alias, salary_slip_alias)

	if filters.get("branch"):
		conditions.append(f"{branch_expr} = %(branch)s")
		values["branch"] = filters.branch

	if filters.get("employment_type"):
		conditions.append(f"{employee_alias}.employment_type = %(employment_type)s")
		values["employment_type"] = filters.employment_type

	if filters.get("cost_center") and has_column("Salary Slip", "cost_center"):
		conditions.append(f"{salary_slip_alias}.cost_center = %(cost_center)s")
		values["cost_center"] = filters.cost_center

	return conditions


def get_ot_join(values, value_key="ot_components"):
	values[value_key] = tuple(OT_SALARY_COMPONENTS)

	return f"""
		LEFT JOIN (
			SELECT
				parent,
				SUM(amount) AS ot_amount
			FROM `tabSalary Detail`
			WHERE parenttype = 'Salary Slip'
			  AND salary_component IN %({value_key})s
			GROUP BY parent
		) ot
			ON ot.parent = ss.name
	"""

def get_salary_payable_summary(filters):
	conditions = [
		"p.docstatus = 1",
	]

	values = {}

	if filters.get("fiscal_year"):
		conditions.append("i.fiscal_year = %(fiscal_year)s")
		values["fiscal_year"] = filters.fiscal_year

	if filters.get("month"):
		conditions.append("i.month = %(month)s")
		values["month"] = filters.month

	if filters.get("branch"):
		conditions.append("p.branch = %(branch)s")
		values["branch"] = filters.branch

	if filters.get("employment_type"):
		conditions.append("""
			CASE
				WHEN TRIM(p.employee_type) = 'DFG Trainer' THEN 'DFG'
				ELSE TRIM(p.employee_type)
			END = %(employment_type)s
		""")
		values["employment_type"] = filters.employment_type

	where_clause = " AND ".join(conditions)

	employee_type_expr = """
		CASE
			WHEN TRIM(p.employee_type) = 'DFG Trainer' THEN 'DFG'
			ELSE TRIM(p.employee_type)
		END
	"""

	gross_expr = "(IFNULL(i.total_wage, 0) + IFNULL(i.total_ot_amount, 0))"

	return frappe.db.sql(
		f"""
		SELECT
			'Musterroll/OAP/Operator/GFG/DFG' AS section,
			COALESCE(p.branch, 'No Branch') AS branch,
			COALESCE({employee_type_expr}, 'No Employee Type') AS category,
			NULL AS employee,
			NULL AS employee_name,
			COUNT(DISTINCT i.employee) AS employee_count,

			SUM({gross_expr}) AS net_pay,
			SUM(IFNULL(i.total_wage, 0)) AS total_wage,
			SUM(IFNULL(i.total_ot_amount, 0)) AS ot_amount,
			SUM({gross_expr}) AS gross_pay,

			0 AS consultant_paid,
			SUM({gross_expr}) AS total_amount

		FROM `tabMR Payment Item` AS i
		INNER JOIN `tabProcess MR Payment` AS p
			ON i.parent = p.name
		WHERE {where_clause}
		GROUP BY p.branch, {employee_type_expr}
		ORDER BY p.branch, {employee_type_expr}
		""",
		values,
		as_dict=True,
	)

def get_salary_payable_detail(filters):
	conditions = [
		"p.docstatus = 1",
	]

	values = {}

	if filters.get("fiscal_year"):
		conditions.append("i.fiscal_year = %(fiscal_year)s")
		values["fiscal_year"] = filters.fiscal_year

	if filters.get("month"):
		conditions.append("i.month = %(month)s")
		values["month"] = filters.month

	if filters.get("branch"):
		conditions.append("p.branch = %(branch)s")
		values["branch"] = filters.branch

	if filters.get("employment_type"):
		conditions.append("""
			CASE
				WHEN TRIM(p.employee_type) = 'DFG Trainer' THEN 'DFG'
				ELSE TRIM(p.employee_type)
			END = %(employment_type)s
		""")
		values["employment_type"] = filters.employment_type

	where_clause = " AND ".join(conditions)

	employee_type_expr = """
		CASE
			WHEN TRIM(p.employee_type) = 'DFG Trainer' THEN 'DFG'
			ELSE TRIM(p.employee_type)
		END
	"""

	gross_expr = "(IFNULL(i.total_wage, 0) + IFNULL(i.total_ot_amount, 0))"

	return frappe.db.sql(
		f"""
		SELECT
			'  Musterroll/OAP/Operator/GFG/DFG Detail' AS section,
			COALESCE(p.branch, 'No Branch') AS branch,
			COALESCE({employee_type_expr}, 'No Employee Type') AS category,
			i.employee AS employee,
			i.person_name AS employee_name,
			1 AS employee_count,

			{gross_expr} AS net_pay,
			IFNULL(i.total_wage, 0) AS total_wage,
			IFNULL(i.total_ot_amount, 0) AS ot_amount,
			{gross_expr} AS gross_pay,

			0 AS consultant_paid,
			{gross_expr} AS total_amount

		FROM `tabMR Payment Item` AS i
		INNER JOIN `tabProcess MR Payment` AS p
			ON i.parent = p.name
		WHERE {where_clause}
		ORDER BY p.branch, {employee_type_expr}, i.employee
		""",
		values,
		as_dict=True,
	)

def get_consultant_je_summary(filters):
	if not filters.get("consultant_account"):
		return []

	from_date, to_date = get_period(filters)

	values = {
		"company": filters.company,
		"from_date": from_date,
		"to_date": to_date,
		"consultant_account": filters.consultant_account,
	}

	conditions = [
		"je.docstatus = 1",
		"je.company = %(company)s",
		"je.posting_date BETWEEN %(from_date)s AND %(to_date)s",
		"jea.account = %(consultant_account)s",
	]

	if filters.get("cost_center"):
		conditions.append("jea.cost_center = %(cost_center)s")
		values["cost_center"] = filters.cost_center

	# Only apply branch filter on Journal Entry Account if you have custom branch field there
	if filters.get("branch") and has_column("Journal Entry Account", "branch"):
		conditions.append("jea.branch = %(branch)s")
		values["branch"] = filters.branch

	where_clause = " AND ".join(conditions)

	return frappe.db.sql(
		f"""
		SELECT
			'Consultant Payment through Journal Entry' AS section,
			COALESCE(jea.cost_center, 'No Cost Center') AS branch,
			'Consultant' AS category,
			NULL AS employee,
			NULL AS employee_name,
			0 AS employee_count,
			0 AS net_pay,
			0 AS total_wage,
			0 AS ot_amount,
			0 AS gross_pay,
			SUM(jea.debit_in_account_currency - jea.credit_in_account_currency) AS consultant_paid,
			SUM(jea.debit_in_account_currency - jea.credit_in_account_currency) AS total_amount
		FROM `tabJournal Entry Account` jea
		INNER JOIN `tabJournal Entry` je
			ON je.name = jea.parent
		WHERE {where_clause}
		GROUP BY jea.cost_center
		ORDER BY jea.cost_center
		""",
		values,
		as_dict=True,
	)


def get_section_total_row(label, rows):
	return {
		"section": label,
		"branch": "",
		"category": "",
		"employee": "",
		"employee_name": "",
		"employee_count": sum(flt(d.get("employee_count")) for d in rows),
		"net_pay": sum(flt(d.get("net_pay")) for d in rows),
		"total_wage": sum(flt(d.get("total_wage")) for d in rows),
		"ot_amount": sum(flt(d.get("ot_amount")) for d in rows),
		"gross_pay": sum(flt(d.get("gross_pay")) for d in rows),
		"consultant_paid": sum(flt(d.get("consultant_paid")) for d in rows),
		"total_amount": sum(flt(d.get("total_amount")) for d in rows),
		"is_total_row": 1,
	}


def get_grand_total_row(rows):
	total_rows = [
		d for d in rows
		if cstr(d.get("section")).startswith("Sub Total")
	]

	return {
		"section": "Grand Total",
		"branch": "",
		"category": "",
		"employee": "",
		"employee_name": "",
		"employee_count": sum(flt(d.get("employee_count")) for d in total_rows),
		"net_pay": sum(flt(d.get("net_pay")) for d in total_rows),
		"total_wage": sum(flt(d.get("total_wage")) for d in total_rows),
		"ot_amount": sum(flt(d.get("ot_amount")) for d in total_rows),
		"gross_pay": sum(flt(d.get("gross_pay")) for d in total_rows),
		"consultant_paid": sum(flt(d.get("consultant_paid")) for d in total_rows),
		"total_amount": sum(flt(d.get("total_amount")) for d in total_rows),
		"is_total_row": 1,
	}


def cstr(value):
	return str(value or "")

def get_mr_employee_type_expr():
	return """
		CASE
			WHEN TRIM(p.employee_type) = 'DFG Trainer' THEN 'DFG'
			ELSE TRIM(p.employee_type)
		END
	"""