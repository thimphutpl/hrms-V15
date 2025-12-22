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
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, date=self.promotion_date)

		if self.revised_ctc:
			employee.ctc = self.revised_ctc

		employee.save()

		promote_to_grade = None
		for pr in self.promotion_details:
			if pr.property == "Grade":
				promote_to_grade = pr.new
		new_basic_pay = frappe.db.get_value("Promotion Employee Detail", {"parent": self.promotion_entry, "employee": self.employee, "docstatus": 1}, "new_basic_pay")
		if not promote_to_grade:
			frappe.throw("Grade details not found in Table.")
		salary_structure = frappe.db.sql("select ss.name from `tabSalary Structure` ss where ss.employee = '{0}' and ss.is_active = 'Yes'".format(self.employee),as_dict = True)
		sst = frappe.get_doc("Salary Structure", salary_structure[0].name)
		sst.fixed_allowance = frappe.db.get_value("Employee Grade", promote_to_grade, "fixed_allowance")
		sst.update_salary_structure(new_basic_pay)
		sst.save(ignore_permissions = True)

	def on_cancel(self):
		self.update_employee_master(cancel=True)

	def update_employee_master(self, cancel=False): 
		if cancel:
			for t in frappe.db.get_all("Employee Promotion", {"employee": self.employee, "name": ("!=", self.name),
					"promotion_date": (">", self.promotion_date), "docstatus": ("!=", 2)}):
				frappe.throw(_("You cannot cancel as there is another promotion record {} following this entry").format(frappe.get_desk_link(self.doctype, t.name)), title="Not Permitted")
			employee = frappe.get_doc("Employee", self.employee)
			for a in self.promotion_details:
				if a.property == "Grade":
					employee.grade = a.current
					# new_pro_date = add_years(self.promotion_date,int(frappe.db.get_value("Employee Grade",a.new,"next_promotion_years")))
					# employee.promotion_due_date = employee.promotion_due_date - relativedelta(years=int(frappe.db.get_value("Employee Grade",a.new,"next_promotion_years")))
					employee.promotion_due_date = add_years(employee.promotion_due_date, -1*int(frappe.db.get_value("Employee Grade",a.new,"next_promotion_years")))
				if a.property == "Designation":
					employee.designation = a.current
			employee.save(ignore_permissions=True)
			frappe.db.sql("""delete from `tabEmployee Internal Work History` 
				where reference_doctype = "{}" and reference_docname = "{}"
				""".format(self.doctype, self.name))
		salary_structure = frappe.db.sql("select ss.name from `tabSalary Structure` ss where ss.employee = '{0}' and ss.is_active = 'Yes'".format(self.employee), as_dict=1)
		if not salary_structure:
			frappe.throw("No Active Salary Structure for selected employee.")
		sst = frappe.get_doc("Salary Structure", salary_structure[0].name)
		sst.fixed_allowance = frappe.db.get_value("Employee Grade", self.current_grade, "fixed_allowance")
		current_basic_pay = frappe.db.get_value("Promotion Employee Detail", {"parent": self.promotion_entry, "employee": self.employee}, "current_basic_pay")
		sst.update_salary_structure(current_basic_pay)
		sst.save(ignore_permissions = True)

	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		employee = update_employee_work_history(employee, self.promotion_details, cancel=True)

		if self.revised_ctc:
			employee.ctc = self.current_ctc

		employee.save()
