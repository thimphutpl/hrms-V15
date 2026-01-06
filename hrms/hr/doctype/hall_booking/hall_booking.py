# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.accounts.utils import get_account_currency, flt
from frappe.model.mapper import get_mapped_doc
from erpnext.controllers.accounts_controller import AccountsController
from erpnext.accounts.doctype.business_activity.business_activity import get_default_ba
from erpnext.accounts.accounts_custom_functions import get_company
from erpnext.accounts.general_ledger import make_gl_entries


class HallBooking(AccountsController):
	def validate(self):
		self.customer_name = self.customer
		self.currency = "BTN",
		self.grand_total = self.amount
		query = "select customer, from_date, to_date, hall_type from `tabHall Booking` \
			where from_date between \'" + str(self.from_date) + "\'and \'" + str(self.to_date) + "\' and \
			to_date between \'" + str(self.from_date) + "\'and \'" + str(self.to_date) + "\' and \
			hall_type= \'" + str(self.hall_type) + "\' and docstatus = 1"
		data = frappe.db.sql(query, as_dict=True)
		if data:
			frappe.throw("Hall type <b>{0}</b> has been already booked by <b>{1}</b> from <b>{2}</b> till <b>{3}</b>".format(data[0].hall_type, data[0].customer, data[0].from_date, data[0].to_date))
	def on_submit(self):
		self.company = get_company(self)
		gl_entries = []
		default_ba = get_default_ba()
		if self.amount:
			debit_account = frappe.db.get_single_value("HR Accounts Settings", "debit_account")
			if not debit_account:
				frappe.throw("Setup Debit Account in Hr Accounts Settings")
			credit_account = frappe.db.get_single_value("HR Accounts Settings", "credit_account")
			if not credit_account:
				frappe.throw("Setup Credit Account in Hr Accounts Settings")
			
			debit_currency = get_account_currency(debit_account)
			gl_entries.append(
				self.get_gl_dict({
					"account": debit_account,
					# "against": credit_account,
					"party_type": "Customer",
					"party": self.customer,
					"debit": flt(self.amount),
					"cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
					"business_activity": default_ba,
					"against_voucher_type": "Hall Booking",
					"against_voucher": self.name
				}, debit_currency)
			)
    
			credit_currency = get_account_currency(credit_account)
			gl_entries.append(
				self.get_gl_dict({
					"account": credit_account,
					# "against": debit_account,
					# "party_type": "Customer",
					# "party": self.customer,
					"credit": flt(self.amount),
					"cost_center": frappe.db.get_value("Branch", self.branch, "cost_center"),
					"business_activity": default_ba,
				}, credit_currency)
			)
			# frappe.msgprint(gl_entries)
			make_gl_entries(gl_entries, cancel=(self.docstatus == 2), update_outstanding="No", merge_entries=False)

	def on_cancel(self):
		self.make_gl_entries_on_cancel()

	def make_gl_entries_on_cancel(self, repost_future_gle=True):
		if frappe.db.sql("""select name from `tabGL Entry` where voucher_type=%s
			and voucher_no=%s""", (self.doctype, self.name)):
			for a in frappe.db.sql("""select name from `tabGL Entry` where voucher_type=%s
			and voucher_no=%s""", (self.doctype, self.name),as_dict=1):
				frappe.db.sql("""
					delete from `tabGL Entry` where name = '{}'""".format(a.name))


# @frappe.whitelist()
# def make_direct_payment(source_name, target_doc=None):
# 	def update_docs(obj, target, source_parent):
# 		target.posting_date = obj.posting_date
# 		target.payment_for = "Hall Booking"
# 		target.branch = obj.branch
# 		target.cost_center = frappe.db.get_value("Branch", obj.branch, "cost_center")
# 		target.payment_type = "Receive"
# 		target.business_activity = "Common"
# 		target.party_type: "Customer"
# 		target.party: obj.customer
# 		target.append("references", {
# 				"reference_type": "Hall Booking",
# 				"reference_name": obj.name,
# 				"party": obj.customer,
# 				"party_type": "Customer",
# 				"account": frappe.db.get_single_value("HR Accounts Settings", "debit_account"),
# 				"amount": obj.amount,
# 				"net_amount": obj.amount
# 		})
# 	doc = get_mapped_doc("Hall Booking", source_name, { 
# 		"Hall Booking": {
# 			"doctype": "Payment Entry",
# 			"field_map": {
# 				"total_amount": "payable_amount",
# 			},
# 			"postprocess": update_docs,
# 			"validation": {"docstatus": ["=", 1]}
# 			},
# 		}, target_doc)
# 	return doc

@frappe.whitelist()
def make_direct_payment(source_name, target_doc=None):

	def postprocess(source, target):
		# Basic fields
		target.posting_date = source.posting_date
		target.payment_type = "Receive"
		target.party_type = "Customer"
		target.party = source.customer
		# target.company = get_company(source)

		# Accounts
		target.paid_from = frappe.db.get_single_value("HR Accounts Settings", "debit_account"),
		target.paid_from_account_currency = frappe.db.get_value("Account", frappe.db.get_single_value("HR Accounts Settings", "debit_account"), "account_currency")

		target.paid_to = frappe.db.get_single_value("HR Accounts Settings", "bank_account")
		target.paid_to_account_currency = frappe.db.get_value("Account", frappe.db.get_single_value("HR Accounts Settings", "bank_account"), "account_currency")


		target.cost_center = frappe.db.get_value(
			"Branch", source.branch, "cost_center"
		)

		# Amounts
		target.paid_amount = source.amount
		target.received_amount = source.amount

		# Reference
		target.append("references", {
			"reference_doctype": "Hall Booking",
			"reference_name": source.name,
			"allocated_amount": source.amount
		})

	doc = get_mapped_doc(
		"Hall Booking",
		source_name,
		{
			"Hall Booking": {
				"doctype": "Payment Entry",
				"validation": {
					"docstatus": ["=", 1]
				}
			}
		},
		target_doc,
		postprocess
	)

	return doc