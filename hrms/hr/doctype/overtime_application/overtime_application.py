# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
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
		self.validate_dates()
		self.calculate_totals()
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
	def validate_submitter(self):
		if self.approver != frappe.session.user:
			pass
			#frappe.throw("Only the selected Approver can submit this document")


	##
	# Post journal entry
	##
	def post_journal_entry(self):	
		cost_center = frappe.db.get_value("Employee", self.employee, "cost_center")
		ot_account = frappe.db.get_single_value("HR Accounts Settings", "overtime_account")
		expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		if not cost_center:
			frappe.throw("Setup Cost Center for employee in Employee Information")
		if not expense_bank_account:
			frappe.throw("Setup Default Expense Bank Account for your Branch")
		if not ot_account:
			frappe.throw("Setup Default Overtime Account in HR Account Setting")

		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "Overtime payment for " + self.employee_name + "(" + self.employee + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'Payment Paid against : ' + self.name + " for " + self.employee;
		je.user_remark = 'Payment Paid against : ' + self.name + " for " + self.employee;
		je.posting_date = self.posting_date
		total_amount = self.total_amount
		je.branch = self.branch

		je.append("accounts", {
				"account": expense_bank_account,
				"cost_center": cost_center,
				"credit_in_account_currency": flt(total_amount),
				"credit": flt(total_amount),
			})
		
		je.append("accounts", {
				"account": ot_account,
				"cost_center": cost_center,
				"debit_in_account_currency": flt(total_amount),
				"debit": flt(total_amount),
				"reference_type": self.doctype,
				"reference_name": self.name
			})

		je.insert()

		self.db_set("payment_jv", je.name)
		frappe.msgprint("Bill processed to accounts through journal voucher " + je.name)


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
	
# 	def validate_total_claim_amount(self):
# 		if self.total_amount and flt(self.total_amount) <= 0:
# 			frappe.throw("Total Claim Amount cannot be 0, please process again")

# 	def validate_eligible_creteria(self):
# 		if "Employee" not in frappe.get_roles(frappe.session.user):
# 			frappe.msgprint(_("Only employee of {} can apply for Overtime").format(frappe.bold(self.company)), title="Not Allowed", indicator="red", raise_exception=1)

# 		salary_struc=frappe.db.sql("select name from `tabSalary Structure` where employee='{}' and is_active='Yes'".format(self.employee), as_dict=True)[0].name
# 		if not salary_struc:
# 			frappe.throw("There is no salary strcuture for the employee ")

# 		if cint(frappe.db.get_value('Salary Structure',salary_struc,'eligible_for_overtime_and_payment')) == 0:
# 			frappe.msgprint(_("You are not eligible for overtime"), title="Not Eligible", indicator="red", raise_exception=1)

# 	def calculate_totals(self):			
# 		settings = frappe.get_single("HR Settings")
# 		overtime_limit_type, overtime_limit = settings.overtime_limit_type, flt(settings.overtime_limit)
# 		total_amount = 0
# 		total_hours = 0
# 		for i in self.get("items"):
# 			if i.is_holiday:
# 				i.is_late_night_ot = 0
# 			i.rate = self.rate
# 			if i.is_late_night_ot or i.is_holiday:
# 				i.number_of_hours    = flt(time_diff_in_hours(i.to_date, i.from_date),2)
# 				i.amount             = flt(i.number_of_hours) * flt(flt(i.rate) * 1.5)
# 			else:
# 				i.number_of_hours    = flt(time_diff_in_hours(i.to_date, i.from_date),2)
# 				i.amount             = flt(i.number_of_hours) * flt(i.rate)
				
# 			total_hours += flt(i.number_of_hours)
# 			# if flt(i.number_of_hours) > flt(overtime_limit):
# 			# 	frappe.throw(_("Row#{}: Number of Hours cannot be more than {} hours").format(i.idx, overtime_limit))

# 			# if overtime_limit_type == "Per Day":
# 			# 	month_start_date = add_to_date(i.to_date, days=-1)
# 			# elif overtime_limit_type == "Per Month":
# 			# 	month_start_date = add_to_date(i.to_date, months=-1)
# 			# elif overtime_limit_type == "Per Year":
# 			# 	month_start_date = add_to_date(i.to_date, years=-1)
# 			# i.amount = flt(i.rate) * flt(i.number_of_hours)
# 			total_amount += i.amount
# 		self.actual_hours = flt(total_hours)
# 		# if flt(total_hours) > flt(overtime_limit):
# 		# 	frappe.throw(_("Only {} hours accepted for payment").format(overtime_limit))
# 		# 	self.total_hours = flt(overtime_limit)
# 		# 	self.total_hours_lapsed = flt(total_hours) - flt(overtime_limit)
# 		# else:
# 		self.total_hours = flt(self.actual_hours)
# 		self.total_amount = round(total_amount,0)
# 		self.actual_amount = round(total_amount,0)

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