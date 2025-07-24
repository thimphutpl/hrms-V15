# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HRAccountsSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		bonus_account: DF.Link
		employee_advance_salary: DF.Link
		employee_advance_travel: DF.Link
		employee_contribution_pf: DF.Link
		leave_encashment_account: DF.Link
		leave_encashment_payable: DF.Link | None
		ltc_account: DF.Link
		meeting_and_seminars_in_account: DF.Link
		meeting_and_seminars_out_account: DF.Link
		muster_roll_payable_account: DF.Link | None
		overtime_account: DF.Link
		pbva_account: DF.Link
		salary_payable_account: DF.Link
		salary_tax_account: DF.Link
		sws_credit_account: DF.Link | None
		sws_debit_account: DF.Link | None
		training_incountry_account: DF.Link
		training_outcountry_account: DF.Link
		travel_claim_payable: DF.Link | None
		travel_incountry_account: DF.Link
		travel_outcountry_account: DF.Link
		travel_refundable_account: DF.Link | None
	# end: auto-generated types
	pass

def get_bank_account(branch=None):
	company=frappe.db.get_value("Branch",branch, "company")
	default_bank_account = frappe.db.get_value('Company',company, 'default_bank_account')
	expense_bank_account = None
	if branch:
		expense_bank_account = frappe.db.get_value('Branch', branch, 'expense_bank_account')

	if not expense_bank_account and not default_bank_account:
		frappe.throw(_("Please set <b>Bank Expense Account</b> under <b>Branch</b> master"))
	return expense_bank_account if expense_bank_account else default_bank_account