# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, nowdate
from datetime import datetime
from frappe.model.document import Document


class ContractRenewalApplication(Document):

	def validate(self):
		self.calculate_average()
		action = frappe.request.form.get('action')
		if action == "Forward":
			self.update_date()

	def on_submit(self):
		self.update_employee()

	def on_cancel(self):
		self.update_employee(cancel=True)

	def update_date(self):
		d2 = datetime.strptime(nowdate(), '%Y-%m-%d')
		self.recommendation_date=d2
	
	def calculate_average(self):
		tot=0
		num=0
		year_set=set()
		for i in self.performance:
			tot+=flt(i.rate)
			num+=1
			if i.year in year_set:
				frappe.throw("There cannot be same year in the Performance Rating")
			year_set.add(i.year)
		if tot!=0:
			self.average_rating=flt(tot)/flt(num)
		else:
			self.average_rating=0


	def update_employee(self, cancel=False):
		emp_doc = frappe.get_doc("Employee", self.employee)
		contract_start_date = emp_doc.contract_start_date
		contract_end_date= emp_doc.contract_end_date
		if cancel:
			for child_d in emp_doc.get_all_children():
				if child_d.doctype=='Contract History':
					if emp_doc.contract_start_date==self.start_date and emp_doc.contract_end_date==self.end_date:
						emp_doc.contract_start_date=child_d.start_date
						emp_doc.contract_end_date=child_d.end_date
						frappe.db.sql("delete from `tabContract History` where name = '{}'".format(child_d.name))
	
		else:
			emp_doc.append("contract_summary", {
				"start_date": contract_start_date,
				"end_date": contract_end_date, 
				"grade": emp_doc.grade
			})
		
			emp_doc.contract_start_date=self.start_date
			emp_doc.contract_end_date=self.end_date
			emp_doc.save()

	@frappe.whitelist()
	def update_form_value(self):
		# frappe.throw(str("I am here"))
		emp_doc = frappe.get_doc("Employee", self.employee)

		if len(self.edu_qualification)==0:
			for child in emp_doc.get_all_children():
				if child.doctype=="Employee Education":
					edu_child = frappe.get_doc("Employee Education", child.name)
					# frappe.throw(str(edu_child.course_name))
					self.append("edu_qualification",{
						"school_univ": edu_child.school_univ,
						"level": edu_child.level,
						"course_name": edu_child.course_name,
						"trade": edu_child.trade,
						"year_of_passing": edu_child.year_of_passing,
						"country": edu_child.country,
						"class_per": edu_child.class_per,
						"maj_opt_subj": edu_child.maj_opt_subj
					})
		
		basic_pay= frappe.db.sql("select sd.amount from `tabSalary Detail` sd join `tabSalary Structure` ss on sd.parent=ss.name where ss.employee='{}' and sd.salary_component='Basic Pay'".format(self.employee), as_dict=True)
		if not basic_pay:
			frappe.throw("The meployee doesn't have basic pay component or salary structure")
		
		self.basic_salary=basic_pay[0].amount

		if not emp_doc.reports_to:
			frappe.throw("The reports to for the employee '{}' is not set".format(self.employee))
		self.supervisor=emp_doc.reports_to

		self.supervisor_user= frappe.get_value("Employee", emp_doc.reports_to, "user_id")


	
