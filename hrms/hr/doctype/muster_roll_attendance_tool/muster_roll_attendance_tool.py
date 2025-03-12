# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime
import json

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class MusterRollAttendanceTool(Document):
	pass

@frappe.whitelist()
def get_employees(
	date: str | datetime.date,
	branch: str | None = None,
	company: str | None = None,
) -> dict[str, list]:
	filters = {"status": "Active", "date_of_joining": ["<=", date]}

	for field, value in {"branch": branch, "company": company}.items():
		if value:
			filters[field] = value

	employee_list = frappe.get_list(
		"Muster Roll Employee", fields=["name as employee", "employee_name"], filters=filters, order_by="employee_name"
	)
	
	attendance_list = frappe.get_list(
		"Muster Roll Attendance",
		fields=["employee", "employee_name", "status"],
		filters={
			"attendance_date": date,
			"docstatus": 1,
		},
		order_by="employee_name",
	)

	unmarked_attendance = _get_unmarked_attendance(employee_list, attendance_list)

	return {"marked": attendance_list, "unmarked": unmarked_attendance}

def _get_unmarked_attendance(employee_list: list[dict], attendance_list: list[dict]) -> list[dict]:
	marked_employees = [entry.employee for entry in attendance_list]
	unmarked_attendance = []

	for entry in employee_list:
		if entry.employee not in marked_employees:
			unmarked_attendance.append(entry)

	return unmarked_attendance

@frappe.whitelist()
def mark_employee_attendance(
	employee_list: list | str,
	status: str,
	date: str | datetime.date,
	company: str | None = None,
) -> None:
	if isinstance(employee_list, str):
		employee_list = json.loads(employee_list)

	for employee in employee_list:
	
		attendance = frappe.get_doc(
			dict(
				doctype="Muster Roll Attendance",
				employee=employee,
				attendance_date=getdate(date),
				status=status,
			)
		)
		attendance.insert()
		attendance.submit()