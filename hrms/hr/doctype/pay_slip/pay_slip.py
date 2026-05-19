# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.query_builder import Order
from frappe.query_builder.functions import Count, Sum
from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)


class PaySlip(Document):
	def validate(self):
		# validate_active_employee(self.employee)
		self.check_existing()
		self.get_emp_and_working_day_details()
		self.calculate_amount()

	def on_submit(self):
		pass
	
	def on_cancel(self):
		pass

	def check_existing(self):
		ps = frappe.qb.DocType("Pay Slip")
		query = (
			frappe.qb.from_(ps)
			.select(ps.name)
			.where(
				(ps.start_date == self.start_date)
				& (ps.end_date == self.end_date)
				& (ps.docstatus != 2)
				& (ps.employee == self.employee)
				& (ps.name != self.name)
			)
		)

		if self.muster_roll_payment_entry:
			query = query.where(ps.muster_roll_payment_entry == self.muster_roll_payment_entry)

		ret_exist = query.run()

		if ret_exist:
			frappe.throw(
				_("Pay Slip of employee {0} already created for month {1}").format(self.employee, self.month)
			)

	def calculate_amount(self):
		self.daily_rate = frappe.db.get_value("Muster Roll Employee", self.employee, "daily_rate")
		if not self.daily_rate:
			frappe.throw("Please set Dialy rate for employee {}".format(self.employee))
		
		self.total_earning = flt(self.payment_days) * flt(self.daily_rate)
		self.net_pay = flt(self.total_earning)

	@frappe.whitelist()
	def get_emp_and_working_day_details(self):
		present = 0.0 
		working_days = date_diff(self.end_date, self.start_date) + 1
		self.working_days = working_days

		attendance_details = self.get_employee_attendance(start_date=self.start_date, end_date=self.end_date)
		for d in attendance_details:
			if d.status == "Half Day":
				present += 0.5

			elif d.status == "Present":
				present += 1

		marked_days = len(attendance_details)
		
		self.payment_days = present

	def get_employee_attendance(self, start_date, end_date):
		attendance = frappe.qb.DocType("Attendance Others")

		attendance_details = (
			frappe.qb.from_(attendance)
			.select(attendance.date, attendance.status)
			.where(
				(attendance.status.isin(["Absent", "Present"]))
				& (attendance.employee == self.employee)
				& (attendance.docstatus == 1)
				& (attendance.date.between(start_date, end_date))
			)
		).run(as_dict=True)

		return attendance_details
