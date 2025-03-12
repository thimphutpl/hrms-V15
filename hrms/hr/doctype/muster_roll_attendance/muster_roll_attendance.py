# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.utils import (
	add_days,
	cint,
	cstr,
	format_date,
	get_datetime,
	get_link_to_form,
	getdate,
	nowdate,
)
from erpnext.setup.doctype.employee.employee import (
	InactiveEmployeeStatusError,
	get_holiday_list_for_employee,
)

class DuplicateAttendanceError(frappe.ValidationError):
	pass

class MusterRollAttendance(Document):
	def validate(self):
		from erpnext.controllers.status_updater import validate_status

		validate_status(self.status, ["Present", "Absent", "Half Day"])
		validate_active_mr_employee(self.employee)
		self.validate_attendance_date()
		self.validate_duplicate_record()
		self.validate_employee_status()

	def validate_attendance_date(self):
		date_of_joining = frappe.db.get_value("Muster Roll Employee", self.employee, "date_of_joining")

		if date_of_joining and getdate(self.attendance_date) < getdate(date_of_joining):
			frappe.throw(
				_("Attendance date {0} can not be less than employee {1}'s joining date: {2}").format(
					frappe.bold(format_date(self.attendance_date)),
					frappe.bold(self.employee),
					frappe.bold(format_date(date_of_joining)),
				)
			)

	def validate_duplicate_record(self):
		duplicate = self.get_duplicate_attendance_record()

		if duplicate:
			frappe.throw(
				_("Attendance for employee {0} is already marked for the date {1}: {2}").format(
					frappe.bold(self.employee),
					frappe.bold(format_date(self.attendance_date)),
					get_link_to_form("Muster Roll Attendance", duplicate),
				),
				title=_("Duplicate Attendance"),
				exc=DuplicateAttendanceError,
			)

	def get_duplicate_attendance_record(self) -> str | None:
		Attendance = frappe.qb.DocType("Muster Roll Attendance")
		query = (
			frappe.qb.from_(Attendance)
			.select(Attendance.name)
			.where(
				(Attendance.employee == self.employee)
				& (Attendance.docstatus < 2)
				& (Attendance.attendance_date == self.attendance_date)
				& (Attendance.name != self.name)
			)
			.for_update()
		)

		duplicate = query.run(pluck=True)

		return duplicate[0] if duplicate else None

	def validate_employee_status(self):
		if frappe.db.get_value("Muster Roll Employee", self.employee, "status") == "Inactive":
			frappe.throw(_("Cannot mark attendance for an Inactive employee {0}").format(self.employee))

def validate_active_mr_employee(employee, method=None):
	if isinstance(employee, dict | Document):
		employee = employee.get("employee")

	if employee and frappe.db.get_value("Muster Roll Employee", employee, "status") == "Inactive":
		frappe.throw(
			_("Transactions cannot be created for an Inactive Muster Roll Employee {0}.").format(
				get_link_to_form("Muster Roll Employee", employee)
			),
			InactiveEmployeeStatusError,
		)