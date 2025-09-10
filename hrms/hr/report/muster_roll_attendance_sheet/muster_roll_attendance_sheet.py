# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from calendar import monthrange
from itertools import groupby

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Extract, Sum
from frappe.utils import cint, cstr, getdate
from frappe.utils.nestedset import get_descendants_of

Filters = frappe._dict

status_map = {
	"Present": "P",
	"Absent": "A",
	"Half Day": "HD",
}

day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def execute(filters: Filters | None = None) -> tuple:
	filters = frappe._dict(filters or {})

	if not (filters.month and filters.year):
		frappe.throw(_("Please select month and year."))

	if not filters.company:
		frappe.throw(_("Please select company."))

	attendance_map = get_attendance_map(filters)

	if not attendance_map:
		frappe.msgprint(_("No attendance records found."), alert=True, indicator="orange")
		return [], [], None, None

	columns = get_columns(filters)
	data = get_data(filters, attendance_map)

	if not data:
		frappe.msgprint(_("No attendance records found for this criteria."), alert=True, indicator="orange")
		return columns, [], None, None

	# message = get_message() if not filters.summarized_view else ""
	# chart = get_chart_data(attendance_map, filters)

	return columns, data

def get_columns(filters: Filters) -> list[dict]:
	columns = []

	columns.extend(
		[
			{
				"label": _("Employee"),
				"fieldname": "employee",
				"fieldtype": "Link",
				"options": "Muster Roll Employee",
				"width": 180,
			},
			{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		]
	)

	columns.extend(get_columns_for_days(filters))

	return columns

def get_columns_for_days(filters: Filters) -> list[dict]:
	total_days = get_total_days_in_month(filters)
	days = []

	for day in range(1, total_days + 1):
		day = cstr(day)
		# forms the dates from selected year and month from filters
		date = f"{cstr(filters.year)}-{cstr(filters.month)}-{day}"
		# gets abbr from weekday number
		weekday = day_abbr[getdate(date).weekday()]
		# sets days as 1 Mon, 2 Tue, 3 Wed
		label = f"{day} {weekday}"
		days.append({"label": label, "fieldtype": "Data", "fieldname": day, "width": 80})

	return days

def get_total_days_in_month(filters: Filters) -> int:
	return monthrange(cint(filters.year), cint(filters.month))[1]

def get_data(filters: Filters, attendance_map: dict) -> list[dict]:
	employee_details = get_employee_related_details(filters)
	data = []

	data = get_rows(employee_details, filters, attendance_map)

	return data

def get_employee_related_details(filters: Filters) -> tuple[dict, list]:
	Employee = frappe.qb.DocType("Muster Roll Employee")
	query = (
		frappe.qb.from_(Employee)
		.select(
			Employee.name,
			Employee.employee_name,
			Employee.branch,
			Employee.company,
		)
		.where(
			Employee.company == filters.company
		)
	)

	if filters.employee:
		query = query.where(Employee.name == filters.employee)

	employee_details = query.run(as_dict=True)

	emp_map = {}

	for emp in employee_details:
		emp_map[emp.name] = emp

	return emp_map

def get_rows(employee_details: dict, filters: Filters, attendance_map: dict) -> list[dict]:
	records = []
	
	for employee, details in employee_details.items():
		employee_attendance = attendance_map.get(employee)
		if not employee_attendance:
			continue

		attendance_for_employee = get_attendance_status_for_detailed_view(
			employee, filters, employee_attendance
		)
		# set employee details in the first row
		attendance_for_employee[0].update({"employee": employee, "employee_name": details.employee_name})

		records.extend(attendance_for_employee)

	return records

def get_attendance_status_for_detailed_view(
	employee: str, filters: Filters, employee_attendance: dict) -> list[dict]:
	"""Returns list of shift-wise attendance status for employee
	[
	        {'shift': 'Morning Shift', 1: 'A', 2: 'P', 3: 'A'....},
	        {'shift': 'Evening Shift', 1: 'P', 2: 'A', 3: 'P'....}
	]
	"""
	total_days = get_total_days_in_month(filters)
	attendance_values = []

	row = {}
	for day in range(1, total_days + 1):
		status = employee_attendance.get(day)
		abbr = status_map.get(status, "")
		row[cstr(day)] = abbr

	attendance_values.append(row)
	return attendance_values

def get_attendance_map(filters: Filters) -> dict:
	attendance_list = get_attendance_records(filters)

	attendance_map = {}

	for d in attendance_list:
		attendance_map.setdefault(d.employee, {})
		attendance_map[d.employee][d.day_of_month] = d.status

	return attendance_map

def get_attendance_records(filters: Filters) -> list[dict]:
	Attendance = frappe.qb.DocType("Muster Roll Attendance")
	query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.employee,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.status,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	)

	if filters.employee:
		query = query.where(Attendance.employee == filters.employee)
	query = query.orderby(Attendance.employee, Attendance.attendance_date)

	return query.run(as_dict=1)