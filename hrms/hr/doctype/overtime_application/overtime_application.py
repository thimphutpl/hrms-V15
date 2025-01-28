# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate,flt,cint,today,add_to_date,time_diff_in_hours,nowdate
from frappe.model.document import Document
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from datetime import datetime
from erpnext.custom_workflow import verify_workflow

class OvertimeApplication(Document):	
	def validate(self):
		validate_workflow_states(self)
		self.validate_dates()
		self.calculate_totals()
		self.validate_employee_grade()
		verify_workflow(self)

	def on_submit(self):
		#self.check_status()
		self.validate_submitter()
		 	#self.check_budget()
		#self.post_journal_entry()

	def on_cancel(self):
		self.check_journal()
	
	def check_budget(self):
		cc = get_branch_cc(self.branch)
		account = frappe.db.get_single_value ("HR Accounts Settings", "overtime_account")

		check_budget_available(cc, account, self.posting_date, self.total_amount, throw_error=True)		

	def calculate_totals(self):		
		total_hours  = 0
		for i in self.items:
				total_hours += flt(i.number_of_hours)

		self.total_hours  = flt(total_hours)
		self.total_amount = round(flt(total_hours)*flt(self.rate),0)

		if flt(self.total_hours) <= 0:
			frappe.throw(_(" <b> From Time cannot be greater than to time </b> "),title="Wrong Input")

				
	def check_status(self):
		if self.status != "Approved":
			frappe.throw("Only Approved documents can be submitted")
	
	##
	# Dont allow duplicate dates
	##
	def validate_dates(self):
		self.posting_date = nowdate()
		'''
		if self.posting_date > nowdate():
				frappe.throw(_("Posting date cannot be a future date."), title="Invalid Date")
		'''
				
		for a in self.items:
			if not a.from_date or not a.to_date:
				frappe.throw(_("Row#{0} : Date cannot be blank").format(a.idx),title="Invalid Date")

			if str(getdate(a.to_date)) > str(nowdate()):
				frappe.throw(_("Row#{0} : Future dates are not accepted").format(a.idx), title="Invalid Date")
					
			for b in self.items:
				if a.to_date == b.to_date and a.idx != b.idx:
					frappe.throw("Duplicate Dates in row " + str(a.idx) + " and " + str(b.idx))
	##
	# Allow only the approver to submit the document
	##

	def validate_employee_grade(self):		
		allowed_grades = ['O1', 'O2', 'O3', 'O4', 'O5', 'O6', 'O7']
		# Fetch the employee's grade
		employee = frappe.get_doc('Employee', self.employee)		
		if not employee.grade:
			frappe.throw(_("The selected employee does not have a grade assigned."))
		if employee.grade not in allowed_grades:
			frappe.throw(_("Overtime Application can only be processed for employees with grades O1 to O8. Your Current grade is: {0}").format(employee.grade))

	def validate_submitter(self):
		if self.approver != frappe.session.user:
			pass
			#frappe.throw("Only the selected Approver can submit this document")


	##
	# Check journal entry status (allow to cancel only if the JV is cancelled too)
	##
	def check_journal(self):
		cl_status = frappe.db.get_value("Journal Entry", self.payment_jv, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the journal entry " + str(self.payment_jv) + " first!")
		
	##
	# Check journal entry status (allow to cancel only if the JV is cancelled too)
	##
	def check_journal(self):
		cl_status = frappe.db.get_value("Journal Entry", self.payment_jv, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the journal entry " + str(self.payment_jv) + " first!")
		
		self.db_set("payment_jv", None)

# 	def validate(self):
# 		# validate_workflow_states(self)
# 		self.validate_dates()
# 		self.calculate_totals()
# 		self.validate_eligible_creteria()
# 		# if self.workflow_state != "Approved":
# 		# 	notify_workflow_states(self)
# 		self.processed = 0
# 		self.validate_total_claim_amount()
	
		self.db_set("payment_jv", None)

# 	def on_cancel(self):
# 		# notify_workflow_states(self)
# 		self.update_salary_structure(True)

# 	def on_submit(self):
# 		self.update_salary_structure()
		
# 		# notify_workflow_states(self)
# 	def update_salary_structure(self, cancel=False):
# 		if cancel:
# 			rem_list = []
# 			if self.salary_structure:
# 				doc = frappe.get_doc("Salary Structure", self.salary_structure)
# 				for d in doc.get("earnings"):
# 					if d.salary_component == self.salary_component and self.name in (d.reference_number, d.ref_docname):
# 						rem_list.append(d)

# 				[doc.remove(d) for d in rem_list]
# 				doc.save(ignore_permissions=True)
# 		else:
# 			if frappe.db.exists("Salary Structure", {"employee": self.employee, "is_active": "Yes"}):
# 				doc = frappe.get_doc("Salary Structure", {"employee": self.employee, "is_active": "Yes"})
# 				row = doc.append("earnings",{})
# 				row.salary_component        = "Overtime Allowance"
# 				# row.from_date               = self.recovery_start_date
# 				# row.to_date                 = self.recovery_end_date
# 				row.amount                  = flt(self.total_amount)
# 				row.default_amount          = flt(self.total_amount)
# 				row.reference_number        = self.name
# 				row.ref_docname             = self.name
# 				row.total_days_in_month     = 0
# 				row.working_days            = 0
# 				row.leave_without_pay       = 0
# 				row.payment_days            = 0
# 				doc.save(ignore_permissions=True)
# 				# self.db_set("salary_structure", doc.name)
# 			else:
# 				frappe.throw(_("No active salary structure found for employee {0} {1}").format(self.employee, self.employee_name), title="No Data Found")

# 	# Dont allow duplicate dates
# 	def validate_dates(self):				
# 		self.posting_date = nowdate()
				  
# 		for a in self.items:
# 			if not a.date:
# 				frappe.throw(_("Row#{0} : Date cannot be blank").format(a.idx),title="Invalid Date")

# 			if str(a.date) > str(nowdate()):
# 				frappe.throw(_("Row#{0} : Future dates are not accepted").format(a.idx), title="Invalid Date")

# 			#Validate if time interval falls between another time interval for the same date   
# 			for b in self.items:
# 				if a.date == b.date and a.idx != b.idx:
# 					time_format = "%H:%M:%S"
# 					start1 = datetime.strptime(a.from_time, time_format)
# 					end1 = datetime.strptime(a.to_time, time_format)
# 					start2 = datetime.strptime(b.from_time, time_format)
# 					end2 = datetime.strptime(b.to_time, time_format)
# 					#frappe.throw("{}, {}, {} and {},{},{}".format(start2,start1,end2,start2,end1,end2))
# 					if start2 <= start1 <= end2 or start2 <= end1 <= end2:
# 						frappe.throw("Duplicate Dates in row " + str(a.idx) + " and " + str(b.idx))

# def get_permission_query_conditions(user):
# 	if not user: user = frappe.session.user
# 	user_roles = frappe.get_roles(user)

# 	if user == "Administrator":
# 		return
# 	if "HR User" in user_roles or "HR Manager" in user_roles:
# 		return

# 	return """(
# 		`tabOvertime Application`.owner = '{user}'
# 		or
# 		exists(select 1
# 				from `tabEmployee`
# 				where `tabEmployee`.name = `tabOvertime Application`.employee
# 				and `tabEmployee`.user_id = '{user}')
# 		or
# 		(`tabOvertime Application`.approver = '{user}' and `tabOvertime Application`.workflow_state not in ('Draft','Approved','Rejected','Cancelled'))
# 	)""".format(user=user)