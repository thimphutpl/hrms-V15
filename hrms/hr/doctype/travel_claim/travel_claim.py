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
		self.validate_dsa_ceiling()
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
	def before_cancel(self):
		self.unlink_travel_authorization()
		for a in str(self.claim_journal).split(", "):
			je_doc = frappe.get_doc("Journal Entry", a)
			if je_doc.docstatus == 1:
				je_doc.cancel()
			elif je_doc.docstatus == 0:
				je_doc.delete_doc(ignore_permissions=True)
		frappe.db.sql("update `tabGL Entry` set voucher_no = NULL where voucher_no = '{}'".format(self.name))
		frappe.db.sql("update `tabGL Entry` set against_voucher = NULL where against_voucher = '{}'".format(self.name))
		frappe.db.sql("update `tabPayment Ledger Entry` set voucher_no = NULL where voucher_no = '{}'".format(self.name))
		frappe.db.sql("update `tabPayment Ledger Entry` set against_voucher_no = NULL where against_voucher_no = '{}'".format(self.name))
	def on_cancel(self):
		self.check_journal_entry()
		if self.training_event:
			self.update_training_event(cancel=True)
		self.db_set("workflow_state", "Cancelled")
	def unlink_travel_authorization(self):
		if self.travel_authorization:
			travel_a = frappe.get_doc("Travel Authorization", self.travel_authorization)
			travel_a.db_set("travel_claim","")
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
		if self.claim_journal and frappe.db.exists("Journal Entry", {"name": self.claim_journal, "docstatus": ("<","2")}):
			frappe.throw(_("You need to cancel {} first").format(frappe.get_desk_link("Journal Entry", self.claim_journal)))

	def validate_travel_last_day(self):
		if len(self.get("items")) > 1:
			self.items[-1].is_last_day = 1

	def validate_dsa_ceiling(self):
		max_days_per_month  = 0
		tt_list = []
		local_count = {}
		claimed_count = {}
		mapped_count = {}
		months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
		cond1 = ""
		cond2 = ""
		cond3 = ""
		format_string = ""
		lastday_dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
		
		if self.place_type.lower().replace("-","") == "incountry":
			max_days_per_month = frappe.db.get_single_value("HR Settings", "max_days_incountry")
			if max_days_per_month:
				tt_list = frappe.db.sql_list("select travel_type from `tabHR Settings Incountry`")
		else:
			max_days_per_month = frappe.db.get_single_value("HR Settings", "max_days_outcountry")
			if max_days_per_month:
				tt_list = frappe.db.sql_list("select travel_type from `tabHR Settings Outcountry`")

		if tt_list:
			format_string = ("'"+"','".join(['%s'] * len(tt_list))+"'") % tuple(tt_list)
			cond1 += "and t1.travel_type in ({0}) ".format(format_string, self.travel_type)

		if max_days_per_month and (not tt_list or self.travel_type in (format_string)):
			local_count = self.get_monthly_count(self.items)
			for k in local_count:
				cond2 += " '{0}' between date_format(t2.`from_date`,'%Y%m') and date_format(ifnull(t2.`to_date`,t2.`date`),'%Y%m') or".format(k)
			cond2 = cond2.rsplit(' ',1)[0]
			cond2 = "and (" + cond2 + ")"
			cond3 = "and t2.is_last_day = 0" if not lastday_dsa_percent else ""

			query = """
					select
							t2.from_date,
							t2.to_date,
							t2.no_days
					from
							`tabTravel Claim` as t1,
							`tabTravel Claim Item` as t2
					where t1.employee = '{0}'
					and t1.docstatus = 1
					and t1.place_type = '{1}'
					{2}
					and t2.parent = t1.name
					{3}
					{4}
				""".format(self.employee, self.place_type, cond1, cond2, cond3)

			tc_list = frappe.db.sql(query, as_dict=True)

			if tc_list:
				claimed_count = self.get_monthly_count(tc_list)

			for k,v in local_count.items():
				mapped_count[k] = {'local': v, 'claimed': claimed_count.get(k,0), 'balance': flt(max_days_per_month)-flt(claimed_count.get(k,0))}

			for i in self.get("items"):
				i.remarks = ""
				i.days_allocated = 0
				if i.is_last_day and not lastday_dsa_percent:
					i.days_allocated = 0
					continue
				
				record_count = self.get_monthly_count([i])
				for k,v in record_count.items():
					lapsed  = 0
					counter = 0
					if mapped_count[k]['balance'] >= v:
						i.days_allocated = flt(i.days_allocated) + v
						mapped_count[k]['balance'] -= v
					else:
						if mapped_count[k]['balance'] < 0:
							lapsed = v
						else:
							lapsed = v - mapped_count[k]['balance']
							i.days_allocated = flt(i.days_allocated) + mapped_count[k]['balance']
							mapped_count[k]['balance'] = 0
								
						if lapsed:
							counter += 1
							frappe.msgprint(_("Row#{0}: You have crossed the DSA({4} days) limit by {1} days for the month {2}-{3}").format(i.idx, int(lapsed), months[int(str(k)[4:])-1], str(k)[:4],max_days_per_month))
							i.remarks = str(i.remarks)+"{3}) {0} Day(s) lapsed for the month {1}-{2}\n".format(int(lapsed), months[int(str(k)[4:])-1], str(k)[:4], counter)
		else:
			for i in self.get("items"):
				i.remarks = ""
				i.days_allocated = 0 if i.is_last_day and not lastday_dsa_percent else i.no_days 

	def update_amounts(self):
		lastday_dsa_percent = flt(frappe.db.get_single_value("HR Settings", "return_day_dsa")) 
		total_claim_amount = 0
		company_currency = frappe.db.get_value("Company", self.company, "default_currency")
		dsa_ceilings = {}
		total_claim_days = 0
		for item in self.get("items"):
			# if str(item.date).split("-")[1]==str(item.till_date).split("-")[1]:
			# 	if str(item.date).split("-")[1] not in dsa_ceilings:
			# 		dsa_ceilings.update({str(item.date).split("-")[1]: {"days": date_diff(item.till_date, item.date)+1}})
			# 	else:
			# 		dsa_ceilings[str(item.date).split("-")[1]]['days'] += date_diff(item.till_date, item.date)+1
			# else:
			# 	for m in range(int(str(item.date).split("-")[1]), int(str(item.till_date).split("-")[1])+1):
			# 		if m == int(str(item.date).split("-")[1]):
			# 			if str(item.date).split("-")[1] not in dsa_ceilings:
			# 				dsa_ceilings.update({str(item.date).split("-")[1]: {"days": date_diff(item, item.date)+1}})
			# 			else:
			# 				dsa_ceilings[str(item.date).split("-")[1]]['days'] += date_diff(item.till_date, item.date)+1
			# 		elif m ==  int(str(item.till_date).split("-")[1]):
			# 			if str(item.date).split("-")[1] not in dsa_ceilings:
			# 				dsa_ceilings.update({str(item.date).split("-")[1]: {"days": date_diff(item.till_date, item.date)+1}})
			# 			else:
			# 				dsa_ceilings[str(item.date).split("-")[1]]['days'] += date_diff(item.till_date, item.date)+1
			# 		else:
			# 			if str(m) not in dsa_ceilings:
			# 				dsa_ceilings.update({str(m): {"days": 15}})
			# 			else:
			# 				dsa_ceilings[str(item.date).split("-")[1]]['days'] += 15
				# exchange_rate = 1 if self.currency == company_currency else get_exchange_rate(self.currency, company_currency)
			item.dsa = flt(item.dsa)
			if item.is_last_day:
				item.dsa_percent = flt(lastday_dsa_percent)
			
			# if self.mode_of_travel == "Personal Car":
			item.amount = (flt(item.days_allocated) * (flt(item.dsa) * flt(item.dsa_percent) / 100) + flt(item.mileage_rate) * flt(item.distance))
			total_claim_days += item.days_allocated
			# else:
			# 	item.amount = flt(item.days_allocated) * (flt(item.dsa) * flt(item.dsa_percent) / 100)
			item.base_amount = flt(item.amount) * flt(self.exchange_rate)
			total_claim_amount += flt(item.base_amount)
		
		self.total_claim_amount = flt(total_claim_amount)
		self.total_claim_days = flt(total_claim_days)
		self.balance_amount = (flt(self.total_claim_amount) + flt(self.extra_claim_amount) - flt(self.advance_amount))
		
		if flt(self.balance_amount) < 0:
			frappe.throw(_("Balance Amount cannot be a negative value."), title="Invalid Amount")

	def get_monthly_count(self, items):
		counts = {}
		for i in items:
			i.to_date = i.from_date if not i.to_date else i.to_date
			from_month = str(i.from_date)[5:7]
			to_month = str(i.to_date)[5:7]
			from_year = str(i.from_date)[:4]
			to_year = str(i.to_date)[:4]
			from_monthyear = str(from_year)+str(from_month)
			to_monthyear = str(to_year)+str(to_month)

			if int(to_monthyear) >= int(from_monthyear):
				for y in range(int(from_year), int(to_year)+1):
					m_start = from_month if str(y) == str(from_year) else '01'
					m_end = to_month if str(y) == str(to_year) else '12'
									
					for m in range(int(m_start), int(m_end)+1):
						key = str(y)+str(m).rjust(2,str('0'))
						m_start_date = key[:4]+'-'+key[4:]+'-01'
						m_start_date = i.from_date if str(y)+str(m).rjust(2,str('0')) == str(from_year)+str(from_month) else m_start_date
						m_end_date = i.to_date if str(y)+str(m).rjust(2,str('0')) == str(to_year)+str(to_month) else get_last_day(m_start_date)
						if key in counts:
							counts[key] += date_diff(m_end_date, m_start_date)+1
						else:
							counts[key] = date_diff(m_end_date, m_start_date)+1
			else:
				frappe.throw(_("Row#{0} : Till Date cannot be before from date.").format(i.idx), title="Invalid Data")
		return collections.OrderedDict(sorted(counts.items()))
		
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
		payable_account = frappe.db.get_single_value("HR Accounts Settings", 'travel_claim_payable')
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

	if "HR Master" in user_roles or "HR Manager" in user_roles or "Accounts User" in user_roles or "Accounts Master" in user_roles:
		return

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

