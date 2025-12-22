# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate, getdate, today, add_to_date
from erpnext.custom_utils import check_budget_available, get_branch_cc 
#from erpnext.custom_workflow import verify_workflow_tc
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class OvertimeApplication(Document):
	def validate(self):
		#verify_workflow_tc(self)
		validate_workflow_states(self)
		self.validate_dates()
		#self.validate_overtime_limit()
		self.calculate_totals()
		notify_workflow_states(self)
		# self.set_approver(self)

	def on_submit(self):
		#self.check_status()
		self.validate_overtime_limit()
		self.validate_submitter()
		 	#self.check_budget()
		self.post_journal_entry()
		notify_workflow_states(self)

	def on_cancel_after_draft(self):
		validate_workflow_states(self)
		notify_workflow_states(self)
		
	def on_cancel(self):
		self.check_journal()
		notify_workflow_states(self)

	# def set_approver(self):
	# 	self.approver = 
		
	def check_budget(self):
		cc = get_branch_cc(self.branch)
		account = frappe.db.get_single_value ("HR Accounts Settings", "overtime_account")

		check_budget_available(cc, account, self.posting_date, self.total_amount, throw_error=True)		

	# def validate_overtime_limit(self):
	# 	# overtime limit is mandatory under HR Settings
	# 	settings = frappe.get_single("HR Settings")
	# 	overtime_limit_type, overtime_limit = settings.overtime_limit_type, flt(settings.overtime_limit)
	# 	if not overtime_limit:
	# 		frappe.throw(_("Please set overtime limit in HR Settings"))

	# 	# allow overtime claim only as per overtime_limit_type
	# 	from_date = to_date = ""
	# 	dates = frappe.db.sql("""select min(from_date) from_date, max(to_date) to_date 
	# 				from `tabOvertime Application Item`
	# 				where parent = '{}'
	# 	""".format(self.name), as_dict=True)
	# 	if dates:
	# 		from_date = dates[0].from_date
	# 		to_date = dates[0].to_date

	# 		if overtime_limit_type == "Per Day" and add_to_date(to_date, days=-1) > from_date:
	# 			frappe.throw(_("No.of days between {} and {} cannot be more than a Day").format(from_date, to_date))
	# 		elif overtime_limit_type == "Per Month" and add_to_date(to_date, months=-1) > from_date:
	# 			frappe.throw(_("No.of days between {} and {} cannot be more than a Month").format(from_date, to_date))
	# 		elif overtime_limit_type == "Per Year" and add_to_date(to_date, years=-1) > from_date:
	# 			frappe.throw(_("No.of days between {} and {} cannot be more than a Year").format(from_date, to_date))

	def validate_overtime_limit(self):
		from frappe.utils import flt, add_to_date
		from frappe import _

		# Get HR Settings
		settings = frappe.get_single("HR Settings")
		overtime_limit_type = settings.overtime_limit           # "Per Day", "Per Month", etc.
		overtime_limit = flt(settings.overtime_limit_in_hours) # numerical limit

		if not overtime_limit:
			frappe.throw(_("Please set overtime limit in HR Settings"))

		# Get min and max dates from overtime items
		dates = frappe.db.sql("""
			select min(from_date) as from_date, max(to_date) as to_date 
			from `tabOvertime Application Item`
			where parent = %s
		""", self.name, as_dict=True)

		if dates:
			from_date = dates[0].from_date
			to_date = dates[0].to_date

			# Check if the claimed overtime exceeds the allowed period
			if overtime_limit_type == "Per Day" and add_to_date(to_date, days=-1) > from_date:
				frappe.throw(_("No. of days between {} and {} cannot be more than a Day").format(from_date, to_date))
			elif overtime_limit_type == "Per Month" and add_to_date(to_date, months=-1) > from_date:
				frappe.throw(_("No. of days between {} and {} cannot be more than a Month").format(from_date, to_date))
			elif overtime_limit_type == "Per Year" and add_to_date(to_date, years=-1) > from_date:
				frappe.throw(_("No. of days between {} and {} cannot be more than a Year").format(from_date, to_date))

	# def calculate_totals(self):			
	# 	settings = frappe.get_single("HR Settings")
	# 	overtime_limit_type, overtime_limit = settings.overtime_limit_type, flt(settings.overtime_limit)

	# 	total_hours = 0
	# 	for i in self.get("items"):
	# 		total_hours += flt(i.number_of_hours)
	# 		if flt(i.number_of_hours) > flt(overtime_limit):
	# 			frappe.throw(_("Row#{}: Number of Hours cannot be more than {} hours").format(i.idx, overtime_limit))

	# 		if overtime_limit_type == "Per Day":
	# 			month_start_date = add_to_date(i.to_date, days=-1)
	# 		elif overtime_limit_type == "Per Month":
	# 			month_start_date = add_to_date(i.to_date, months=-1)
	# 		elif overtime_limit_type == "Per Year":
	# 			month_start_date = add_to_date(i.to_date, years=-1)
				
	# 		'''
	# 		ot = frappe.db.sql("""select sum(number_of_hours) 
	# 				from `tabOvertime Application` ot, `tabOvertime Application Item` oti
	# 				where ot.employee = '{}'
	# 				and ot.docstatus = 1
	# 				and oti.parent = ot.name
	# 		""".format(self.employee), as_dict=True)
	# 		'''
		
	# 	self.actual_hours = flt(total_hours)
	# 	if flt(total_hours) > flt(overtime_limit):
	# 			frappe.msgprint(_("Only {} hours accepted for payment").format(overtime_limit))
	# 			self.total_hours = flt(overtime_limit)
	# 			self.total_hours_lapsed = flt(total_hours) - flt(overtime_limit)
	# 	else:
	# 		self.total_hours = flt(self.actual_hours)
	# 	self.total_amount = round(flt(self.total_hours)*flt(self.rate),0)
 
	def calculate_totals(self):
		from frappe.utils import flt, add_to_date
		from frappe import _

		settings = frappe.get_single("HR Settings")
		overtime_limit_type = settings.overtime_limit
		overtime_limit = flt(settings.overtime_limit_in_hours)

		total_hours = 0
		for i in self.get("items"):
			total_hours += flt(i.number_of_hours)
			
			if flt(i.number_of_hours) > overtime_limit:
				frappe.throw(_("Row#{}: Number of Hours cannot be more than {} hours").format(i.idx, overtime_limit))
			
			# Example of using overtime_limit_type if needed for date calculations
			if overtime_limit_type == "Per Day":
				month_start_date = add_to_date(i.to_date, days=-1)
			elif overtime_limit_type == "Per Month":
				month_start_date = add_to_date(i.to_date, months=-1)
			elif overtime_limit_type == "Per Year":
				month_start_date = add_to_date(i.to_date, years=-1)

		self.actual_hours = flt(total_hours)

		if total_hours > overtime_limit:
			frappe.msgprint(_("Only {} hours accepted for payment").format(overtime_limit))
			self.total_hours = overtime_limit
			self.total_hours_lapsed = flt(total_hours) - overtime_limit
		else:
			self.total_hours = self.actual_hours

		self.total_amount = round(flt(self.total_hours) * flt(self.rate), 0)


	def check_status(self):
		if self.status != "Approved":
			frappe.throw("Only Approved documents can be submitted")
	
	##
	# Dont allow duplicate dates
	##
	def validate_dates(self):
		# self.posting_date = nowdate()
				
		for a in self.items:
			if not a.from_date or not a.to_date:
				frappe.throw(_("Row#{} : Date cannot be blank").format(a.idx), title="Invalid Date")
			elif getdate(a.to_date) > getdate(today()) or getdate(a.to_date) > getdate(today()):
				frappe.throw(_("Row#{} : Future dates are not accepted").format(a.idx))
			else:
				pass

			for b in self.items:
				if (a.from_date == b.from_date and a.idx != b.idx) or (a.to_date == b.to_date and a.idx != b.idx):
					frappe.throw(_("Duplicate Dates in rows {}, {}").format(str(a.idx),str(b.idx)))
				elif (a.from_date >= b.from_date and a.from_date <= b.to_date) and a.idx != b.idx:
					frappe.throw(_("Row#{}: From Date/Time is overlapping with Row#{}").format(a.idx, b.idx))
				elif (a.to_date >= b.from_date and a.to_date <= b.to_date) and a.idx != b.idx:
					frappe.throw(_("Row#{}: To Date/Time is overlapping with Row#{}").format(a.idx, b.idx))

			# check if the dates are already claimed
			for i in frappe.db.sql(""" select oa.name from `tabOvertime Application` oa, `tabOvertime Application Item` oai 
						where oa.employee = %(employee)s and oai.parent = oa.name and oa.name != %(name)s and oa.docstatus < 2
						and %(from_date)s <= oai.to_date and %(to_date)s >= oai.from_date
					""", {"employee": self.employee, "name": self.name, "from_date": a.from_date, "to_date": a.to_date}, as_dict=True):
				frappe.throw(_("Row#{}: Dates are overlapping with another request {}").format(a.idx, frappe.get_desk_link("Overtime Application", i.name)))
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
				"reference_name": self.name,
				
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
