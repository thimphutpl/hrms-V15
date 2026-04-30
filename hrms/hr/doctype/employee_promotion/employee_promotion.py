# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from hrms.hr.utils import update_employee_work_history, validate_active_employee


class EmployeePromotion(Document):
	def validate(self):
		validate_active_employee(self.employee)

	def before_submit(self):
		if getdate(self.promotion_date) > getdate():
			frappe.throw(
				_("Employee Promotion cannot be submitted before Promotion Date"),
				frappe.DocstatusTransitionError,
			)

	def on_submit(self):
		# employee = frappe.get_doc("Employee", self.employee)
		# employee = update_employee_work_history(employee, self.promotion_details, date=self.promotion_date)

		# if self.revised_ctc:
		# 	employee.ctc = self.revised_ctc

		# employee.save()

		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, date=self.promotion_date)
		if self.revised_ctc:
		 	employee.ctc = self.revised_ctc
		# employee = update_employee(employee, self.promotion_details, date=self.promotion_date)
		employee.save()
		new_grade = None
		for a in self.promotion_details:
			if a.property == "Grade":
				new_grade = a.new
		salary_structure = frappe.db.sql("select ss.name from `tabSalary Structure` ss where ss.employee = '{0}' and ss.is_active = 'Yes'".format(self.employee),as_dict = True)
		sst = frappe.get_doc("Salary Structure", salary_structure[0].name)
		sst.fixed_allowance = frappe.db.get_value("Employee Grade", new_grade, "fixed_allowance")
		sst.update_salary_structure(self.new_basic_pay)
		sst.save(ignore_permissions = True)
		
	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, cancel=True)

		if self.revised_ctc:
			employee.ctc = self.current_ctc

		employee.save()
