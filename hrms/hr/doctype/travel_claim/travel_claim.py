# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, money_in_words, getdate, date_diff, today, add_days, get_first_day, get_last_day
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
import collections
from erpnext.setup.utils import get_exchange_rate
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from erpnext.accounts.doctype.accounts_settings.accounts_settings import get_bank_account
from datetime import datetime, timedelta


class TravelClaim(Document):
	def validate(self):			
		validate_workflow_states(self)
		self.validate_travel_last_day()
		self.update_amounts()
		self.validate_dates()
		self.validate_duplicate()
		if self.training_event:
			self.update_training_event()

	def on_update(self):
		self.check_double_dates()
		self.check_double_date_inside()

	def on_submit(self):
		self.update_travel_authorization()
		self.post_journal_entry()
		notify_workflow_states(self)

	def before_cancel(self):
		cl_status = frappe.db.get_value("Journal Entry", self.claim_journal, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the claim journal entry first!")
		
		travel_authorization = frappe.get_doc("Travel Authorization", self.travel_authorization)
		travel_authorization.db_set("travel_claim", "")

	def on_cancel(self):		
		self.check_journal_entry()				
		if self.training_event:
			self.update_training_event(cancel=True)
		notify_workflow_states(self)

	def validate_duplicate(self):
		existing = []
		existing = frappe.db.sql("""
			select name from `tabTravel Claim` where name != '{}' and docstatus != 2 and workflow_state != 'Rejected'
			and ta = '{}'
		""".format(self.name, self.travel_authorization), as_dict=True)

		for a in existing:
			frappe.throw("""Another {} already exists for Travel Authorization {}.""".format(frappe.get_desk_link("Travel Claim",a.name), self.travel_authorization))
	
	def get_dates_between(self,start_date, end_date):
		# Convert start_date and end_date to datetime.date if they are strings
		if isinstance(start_date, str):
			start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
		if isinstance(end_date, str):
			end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
		
		dates = []
		current_date = start_date
		while current_date <= end_date:
			dates.append(current_date)
			current_date += timedelta(days=1)
		return dates

	def update_training_event(self, cancel = False):
		if not cancel:
			if frappe.db.get_value("Training Event Employee", self.training_event_child_ref, "travel_claim_id") in (None, ''):
				frappe.db.sql("""
					update `tabTraining Event Employee` set travel_claim_id = '{}' where name = '{}'
					""".format(self.name, self.training_event_child_ref))
		else:
			if frappe.db.get_value("Training Event Employee", self.training_event_child_ref, "travel_claim_id") == self.name:
				frappe.db.sql("""
					update `tabTraining Event Employee` set travel_claim_id = NULL where name = '{}'
					""".format(self.training_event_child_ref))
	
	def check_journal_entry(self):
		if self.claim_journal:
			journal_entries = str(self.claim_journal).split(", ")			
			for index, je in enumerate(journal_entries):				
				docstatus = frappe.db.get_value("Journal Entry", je, "docstatus")				
				if index > 0 and docstatus == 1:
					frappe.throw(f"Cannot cancel this document because Journal Entry {frappe.get_desk_link('Journal Entry', je)} is submitted.")
								
				if docstatus and docstatus != 2:  
					frappe.throw(f"Cancel Journal Entry {frappe.get_desk_link('Journal Entry', je)} before cancelling this document.")
			
			# Clear the field after verification
			self.db_set("claim_journal", None)
		
	def validate_travel_last_day(self):
		if len(self.get("items")) > 1:
			self.items[-1].is_last_day = 1
		
		
	def update_amounts(self):
		total_claim_amount = 0
		return_day_dsa = flt(frappe.db.get_single_value("HR Settings", "return_day_dsa"))
		company_currency = frappe.db.get_value("Company", self.company, "default_currency")
		row_count = len(self.get("items"))
		for idx, item in enumerate(self.get("items"), start=1):
			item.dsa = flt(item.dsa)
			is_last_row = idx == row_count  # Check if it's the last row
			item.mileage_amount = flt(item.mileage_rate) * flt(item.distance) if self.mode_of_travel == "Personal Car" else 0

			# Default amount calculation
			if self.mode_of_travel == "Personal Car":
				item.amount = flt(item.no_days) * item.dsa * (flt(item.dsa_percent) / 100)

			elif self.place_type in ["Out-Country", "In-Country"]:
				item.amount = (
					flt(item.no_days) * item.dsa * (flt(item.dsa_percent) / 100)
					if item.dsa_percent
					else flt(item.no_days) * item.dsa
				)						
			if is_last_row:
				item.amount = flt(item.dsa) * (flt(return_day_dsa) / 100)				
				item.base_amount = flt(item.amount) + item.mileage_amount
			else:
				# Multiply by exchange rate for all other rows
				item.base_amount = flt(item.amount) * flt(self.exchange_rate) + item.mileage_amount
			total_claim_amount += flt(item.base_amount)
		self.total_claim_amount = flt(total_claim_amount)
		self.balance_amount = (
			flt(self.total_claim_amount) + flt(self.extra_claim_amount) - flt(self.advance_amount)
		)

		if self.balance_amount < 0:
			frappe.throw(_("Balance Amount cannot be a negative value."), title="Invalid Amount")

	def check_double_date_inside(self):
		for i in self.get('items'):
			for j in self.get('items'):
				if i.name != j.name and str(i.from_date) <= str(j.to_date) and str(i.to_date) >= str(j.from_date):
					frappe.throw(_("Row#{}: Dates are overlapping with Row#{}").format(i.idx, j.idx))

	def check_double_dates(self):
		if self.items:
			# check if the travel dates are already used in other travel authorization
			tas = frappe.db.sql("""select t3.idx, t1.name, t2.from_date, t2.to_date
					from 
						`tabTravel Claim` t1, 
						`tabTravel Claim Item` t2,
						`tabTravel Claim Item` t3
					where t1.employee = "{employee}"
					and t1.docstatus != 2
					and t1.name != "{travel_claim}"
					and t2.parent = t1.name
					and t3.parent = "{travel_claim}"
					and (
						(t2.from_date <= t3.to_date and t2.to_date >= t3.from_date)
						or
						(t3.from_date <= t2.to_date and t3.to_date >= t2.from_date)
					)
					and t1.workflow_state not like '%Rejected%'
			""".format(travel_claim = self.name, employee = self.employee), as_dict=True)
			for t in tas:
				frappe.throw("Row#{}: The dates in your current Travel Claim have already been claimed in {} between {} and {}"\
					.format(t.idx, frappe.get_desk_link("Travel Claim", t.name), t.from_date, t.to_date))

	def post_journal_entry(self):
		if self.cost_center: 
			cost_center = self.cost_center
		else:
			cost_center = frappe.db.get_value("Employee", self.employee, "cost_center")
		if not cost_center:
			frappe.throw("Setup Cost Center for employee in Employee Master")

		expense_bank_account = get_bank_account(self.branch, self.company)
		if not expense_bank_account:
			frappe.throw("Setup Default Expense Bank Account in {}".format(frappe.get_desk_link("Branch", self.branch)))
		
		gl_account = ""	
		if self.travel_type == "Travel":
			if self.place_type == "In-Country":
				gl_account =  "travel_incountry_account"
			else:
				gl_account = "travel_outcountry_account"
		elif self.travel_type == "Training":
			if self.place_type == "In-Country":
				gl_account = "training_incountry_account"
			else:
				gl_account = "training_outcountry_account"
		else:
			if self.place_type == "In-Country":
				gl_account = "meeting_and_seminars_in_account"
			else:
				gl_account = "meeting_and_seminars_out_account"
		expense_account = frappe.db.get_single_value("HR Accounts Settings", gl_account)
		payable_account = expense_account

		if not expense_account:
			frappe.throw("Setup Travel/Training Accounts in HR Accounts Settings")
		advance_je = frappe.db.get_value("Travel Authorization", self.ta, "need_advance")
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1
		je.title = "Travel Payable (" + self.employee_name + "  " + self.name + ")"
		je.voucher_type = "Journal Entry"
		je.naming_series = "Journal Voucher"
		je.remark = 'Claim payment against : ' + self.name
		je.posting_date = self.posting_date
		je.branch = self.branch
		# default_cc = frappe.db.get_value("Company", self.company, "company_cost_center")
		total_amt = flt(self.total_claim_amount) + flt(self.extra_claim_amount)
		references = {}
		mileage_amount = 0
		for a in self.items:
			#Getting the mileage_rate and distance_covered
			if a.mileage_rate and a.distance:
				mileage_amount+=flt(a.mileage_rate)*flt(a.distance)

		je.append("accounts", {
				"account": expense_account,
				"reference_type": "Travel Claim",
				"reference_name": self.name,
				"cost_center": self.cost_center,
				"debit_in_account_currency": flt(total_amt,2),
				"debit": (flt(total_amt,2)),
			})

		je.append("accounts", {
				"account": payable_account,
				"reference_type": "Travel Claim",
				"reference_name": self.name,
				"cost_center": self.cost_center,
				"credit_in_account_currency": flt(self.balance_amount,2),
				"credit": flt(self.balance_amount,2),
				"party_type": "Employee",
				"party": self.employee, 
			})
		
		advance_amt = flt(self.advance_amount)
		bank_amt = flt(self.balance_amount)

		if (self.advance_amount) > 0:
			advance_account = frappe.db.get_single_value("HR Accounts Settings",  "employee_advance_travel")
			if not advance_account:
				frappe.throw("Setup Advance to Employee (Travel) in HR Accounts Settings")
			if flt(self.balance_amount) <= 0:
				advance_amt = total_amt

			je.append("accounts", {
				"account": advance_account,
				"party_type": "Employee",
				"party": self.employee,
				"reference_type": "Travel Claim",
				"reference_name": self.name,
				"cost_center": cost_center,
				"credit_in_account_currency": advance_amt,
				"credit": advance_amt,
			})

		je.insert()
		je.submit()
		je_references = je.name

		if flt(self.balance_amount) > 0:
			jeb = frappe.new_doc("Journal Entry")
			jeb.flags.ignore_permissions = 1
			jeb.title = "Travel Payment(" + self.employee_name + "  " + self.name + ")"
			jeb.voucher_type = "Bank Entry"
			jeb.naming_series = "Bank Payment Voucher"
			jeb.remark = 'Claim payment against : ' + self.name
			jeb.posting_date = self.posting_date
			jeb.branch = self.branch
			jeb.append("accounts", {
					"account": payable_account,
					"party_type": "Employee",
					"party": self.employee,
					"reference_type": "Journal Entry",
					"reference_name": je.name,
					"cost_center": cost_center,
					"debit_in_account_currency": bank_amt,
					"debit": bank_amt,
				})

			jeb.append("accounts", {
					"account": expense_bank_account,
					"cost_center": cost_center,
					"reference_type": "Travel Claim",
					"reference_name": self.name,
					"credit_in_account_currency": bank_amt,
					"credit": bank_amt,
				})
			jeb.insert()
			je_references = je_references + ", "+ str(jeb.name)
		self.db_set("claim_journal", je_references)

	def update_travel_authorization(self):
		ta = frappe.get_doc("Travel Authorization", self.travel_authorization)
		if ta.travel_claim and ta.travel_claim != self.name:
			frappe.throw("A travel claim <b>" + str(ta.travel_claim) + "</b> has already been created for the authorization")
		ta.db_set("travel_claim", self.name)
	
	def validate_dates(self):
		if self.travel_authorization:
			self.ta_date = frappe.db.get_value("Travel Authorization", self.travel_authorization, "posting_date")
		if str(self.ta_date) > str(self.posting_date):
			frappe.throw("The Travel Claim Date cannot be earlier than Travel Authorization Date")

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)
	permitted_regions = []

	if user == "Administrator":
		return

	if "HR User" in user_roles or "HR Manager" in user_roles or "Accounts User" in user_roles or "Accounts Master" in user_roles:
		return
	if "HR Support" in user_roles:
		return """(
			exists(select 1
					from `tabAssign Branch`, `tabBranch Item`
					where `tabAssign Branch`.name = `tabBranch Item`.parent 
					and `tabBranch Item`.branch = `tabTravel Claim`.branch
					and `tabAssign Branch`.user = '{user}')
			or
			exists(select 1
					from `tabEmployee`
					where `tabEmployee`.branch = `tabTravel Claim`.branch
					and `tabEmployee`.user_id = '{user}')
			)""".format(user=user)

	return """(
		`tabTravel Claim`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabTravel Claim`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabTravel Claim`.approver = '{user}' and `tabTravel Claim`.workflow_state not in ('Draft','Rejected','Rejected By Supervisor','Waiting for Supervisor','Waiting HR','Cancelled'))
	)""".format(user=user)

