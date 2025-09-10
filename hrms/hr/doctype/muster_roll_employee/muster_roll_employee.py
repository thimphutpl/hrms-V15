# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frappe import _
from frappe.model.naming import set_name_by_naming_series, make_autoname


class MusterRollEmployee(Document):
	def autoname(self):
		if self.muster_roll_group == "National":
			if not self.cid_number:
				frappe.throw(_("CID Number is required for National employees."))
			self.name = self.cid_number
		else:
			if not self.passport_number:
				frappe.throw(_("Passport/Work Permit Number is required for International employees."))
			self.name = self.passport_number
		
		if frappe.db.exists("Muster Roll Employee", self.name):
			frappe.throw(_("A Muster Roll Employee with the {} already exists: {}.").format(
				"CID Number" if self.muster_roll_group == "National" else "Passport/Work Permit Number", 
				frappe.get_desk_link("Muster Roll Employee", self.name),
			))
	
	def validate(self):
		self.set_default_bank_account()

	def set_default_bank_account(self):
		if self.get("bank_accounts"):
			default_bank_account = 0
			for a in self.get("bank_accounts"):
				if a.default:
					default_bank_account += 1
					self.bank_name = a.bank
					self.bank_branch = a.bank_branch
					self.bank_account_type = a.bank_account_type
					self.bank_ac_no = a.account_number

			if default_bank_account == 0:
				frappe.throw(_("Please select a default bank account under 'Bank Information'."))
			elif default_bank_account > 1:
				frappe.throw(_("Only one bank account can be set as default. Please review 'Bank Information' and ensure only one account is marked as default."))

