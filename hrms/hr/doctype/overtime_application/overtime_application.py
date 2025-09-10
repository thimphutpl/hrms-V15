# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from erpnext.custom_workflow import validate_workflow_states

class OvertimeApplication(Document):
	def validate(self):
		validate_workflow_states(self)
		self.validate_dates()
		self.calculate_totals()

	def on_submit(self):
		# self.check_status()
		# self.validate_submitter()
		self.post_journal_entry()

	def on_cancel(self):
		self.check_journal()

	def calculate_totals(self):
                total_hours  = 0
                for i in self.items:
                        total_hours += flt(i.number_of_hours)

                self.total_hours  = flt(total_hours)
                self.total_amount = flt(total_hours)*flt(self.rate)

                if flt(self.total_hours) <= 0:
                        frappe.throw(_("Total number of hours cannot be nil."),title="Incomlete information")

                
	# def check_status(self):
	# 	if self.status != "Approved":
	# 		frappe.throw("Only Approved documents can be submitted")
	
	##
	# Dont allow duplicate dates
	##
	def validate_dates(self):
		for a in self.items:
			if not a.date:
					frappe.throw(_("Row#{0} : Data cannot be blank").format(a.idx),title="Invalid Date")
                                
		for b in self.items:
			if a.date == b.date and a.idx != b.idx:
				frappe.throw("Duplicate Dates in row " + str(a.idx) + " and " + str(b.idx))

	##
	# Allow only the approver to submit the document
	##
	# def validate_submitter(self):
	# 	if self.approver != frappe.session.user:
	# 		frappe.throw("Only the selected Approver can submit this document")


	##
	# Post journal entry
	##
	def post_journal_entry(self):	
		cost_center, ba = frappe.db.get_value("Employee", self.employee, ["cost_center", "business_activity"])
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
		je.title = "Payment for Overtime (" + self.employee_name + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'Payment Paid against : ' + self.name;
		je.posting_date = self.posting_date
		total_amount = self.total_amount
		je.branch = self.branch

		je.append("accounts", {
				"account": expense_bank_account,
				"cost_center": cost_center,
				"business_activity": ba,
				"credit_in_account_currency": flt(total_amount),
				"credit": flt(total_amount),
			})
		
		je.append("accounts", {
				"account": ot_account,
				"cost_center": cost_center,
				"business_activity": ba,
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
		
		self.db_set("payment_jv", "")

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabOvertime Application`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabOvertime Application`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabOvertime Application`.approver = '{user}' and `tabOvertime Application`.workflow_state not in ('Draft','Approved','Rejected','Cancelled'))
	)""".format(user=user)
