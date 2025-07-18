# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, money_in_words, getdate
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
from frappe.utils.data import add_days, date_diff, today
from frappe.model.mapper import get_mapped_doc
from datetime import timedelta
# from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from erpnext.accounts.doctype.accounts_settings.accounts_settings import get_bank_account


class BulkTravelAuthorization(Document):
	def validate(self):
		# validate_workflow_states(self)
		# self.set_employee_supervisor()
		self.validate_travel_last_day()
		self.assign_end_date()
		self.validate_advance()
		self.set_travel_period()
		self.check_total_dsa()
		self.validate_travel_dates()
		self.calculate_amounts()
		self.calculate_total_travel_amount()
		if self.training_event:
			self.update_training_event()
		# if self.workflow_state != "Approved":
		# 	notify_workflow_states(self)
		self.update_amounts()

	def on_update(self):
		self.check_date_overlap()
		self.check_leave_applications()

	def on_submit(self):
		# notify_workflow_states(self)
		# self.create_attendance()
		self.post_journal_entry()
		# if self.travel_type=="Training":
		# 	self.update_training_records()

	def on_cancel(self):
		self.ignore_linked_doctypes = (
			"GL Entry",
			"Payment Ledger Entry",
			"Stock Ledger Entry",
			"Repost Item Valuation",
			"Serial and Batch Bundle",
			"GL Entry",
		)
		# self.cancel_attendance()	
		if self.training_event:
			self.update_training_event(cancel=True)
		# notify_workflow_states(self)

	def on_update_after_submit(self):
		if self.travel_claim:
			frappe.throw("Cannot change once claim is created")
		self.check_date_overlap()
		self.check_leave_applications()
		self.db_set("end_date_auth", self.items[len(self.items) - 1].date)
		# self.cancel_attendance()
		# self.create_attendance()

	def check_total_dsa(self):
		for item in self.items:
			from_date = item.from_date
			to_date   = item.from_date if not item.to_date else item.to_date
			item.no_days   = date_diff(to_date, from_date) + 1

			item.dsa_nu_per_day = flt(item.dsa) * flt(item.exchange_rate)
			item.total_dsa = flt(item.dsa_nu_per_day) * flt(item.no_days)	
	
	# def calculate_amounts(self):
	# 	"""Calculate amounts for all employees based on travel items.
	# 	If employee has number_of_days, use that, otherwise use item's no_days."""
	# 	if not self.items or not self.employee_table:
	# 		return
			
	# 	for employee in self.employee_table:
	# 		total_amount = 0.0  
	# 		for item in self.items:
	# 			days = float(employee.number_of_days) if (
	# 				hasattr(employee, 'number_of_days') and 
	# 				employee.number_of_days not in [None, ""]
	# 			) else float(item.no_days)
	# 			frappe.throw(str(days))
	# 			dsa = float(employee.dsa_per_day or 0)
				
	# 			total_amount += days * dsa
		
	# 		employee.amount = round(total_amount)
	
	# server‑side
	def calculate_amounts(self):
		if not self.items or not self.employee_table:
			return

		total_days_all_items = sum(flt(i.no_days) for i in self.items)

		for employee in self.employee_table:
			dsa  = flt(employee.dsa_per_day or 0)
			days = flt(employee.number_of_days) if employee.number_of_days not in (None, "", 0) else total_days_all_items
			employee.amount = round(days * dsa, 2)


	def calculate_total_travel_amount(self):
		"""Sum all employee amounts to update total_travel_amount"""
		if not self.employee_table:
			self.total_travel_amount = 0
			return
		
		total = sum(
			frappe.utils.flt(employee.amount) 
			for employee in self.employee_table 
			if employee.amount
		)
		self.total_travel_amount = total			

	@frappe.whitelist()
	def set_employee_supervisor(self):
		if self.employee:
			reports_to = frappe.db.get_value("Employee", self.employee, "reports_to")
			if not reports_to:
					frappe.throw("Setup Approver for employee in Approver List")
			approver, approver_name, approver_designation = frappe.db.get_value("Employee", reports_to, ["user_id", "employee_name", "designation"])
			# if not approver:
			# 		frappe.throw("Setup Approver for employee in Approver List")
			self.approver = approver,
			self.approver_name = approver_name,
			self.approver_designation = approver_designation
			return approver, approver_name, approver_designation

	@frappe.whitelist()
	def get_employee(self, branch=None):
		self.set('employee_table', [])
		
		# Get all active employees (filtered by branch if specified)
		filters = {'status': 'Active'}
		if branch:
			filters['branch'] = branch
		
		employees = frappe.get_all("Employee",
			fields=[
				'name as employee',
				'employee_name',
				'branch',
				'designation',
				'employment_type',
				'grade',
				'employee_group',
				'bank_name',
				'bank_ac_no'
			],
			filters=filters
		)
		
		# Get DSA rates for all grades in one query
		grades = list(set([emp['grade'] for emp in employees if emp.get('grade')]))
		grade_rates = {}
		
		if grades:
			grade_rates = frappe.get_all("Employee Grade",
				filters={'name': ['in', grades]},
				fields=['name', 'dsa_per_day'],
			)
			grade_rates = {grade['name']: grade['dsa_per_day'] for grade in grade_rates}
		
		# Add DSA rate to each employee
		for emp in employees:
			emp['dsa_per_day'] = grade_rates.get(emp.get('grade')) or 0
		
		self.set('employee_table', employees)	

	def validate_travel_last_day(self):
		for i in self.items:
			i.is_last_day = 0
		if len(self.get("items")) > 1:
			self.items[-1].is_last_day = 1
	
	# def before_cancel(self):
	# 	# self.update_training_records(cancel=True)
	# 	if self.advance_amount:
	# 		for t in frappe.get_all("Journal Entry", ["name"], {"name": self.advance_amount, "docstatus": ("<",2)}):
	# 			msg = '<b>Reference# : <a href="#Form/Journal Entry/{0}">{0}</a></b>'.format(t.name)
	# 			frappe.throw(_("Advance payment for this transaction needs to be cancelled first.<br>{0}").format(msg),title='<div style="color: red;">Not permitted</div>')
	# 	ta = frappe.db.sql("""
	# 		select name from `tabTravel Claim` where ta = '{}' and docstatus != 2
	# 	""".format(self.name))
	# 	if ta:
	# 		frappe.throw("""There is Travel Claim <a href="#Form/Travel%20Claim/{0}"><b>{0}</b></a> linked to this Travel Authorization""".format(ta[0][0]))

	# def update_amounts(self):
	# 	if self.grade:
	# 		dsa_per_day=frappe.db.get_value("Employee Grade", self.grade, "dsa_per_day")
	# 		#frappe.throw(dsa_per_day)
	# 	# lastday_dsa_percent = flt(frappe.db.get_single_value("HR Settings", "return_day_dsa")) 
	# 	total_travel_amount, diff = 0, 0
		
	# 	total_claim_days = 0
	# 	for item in self.get("items"):
	# 		#item.total_dsa=dsa_per_day
	# 		#frappe.msgprint(str(flt(item.days_allocated)))
	# 		item.dsa = flt(item.total_dsa)
	# 		if item.is_last_day or flt(item.days_allocated)==0.0:
	# 			item.dsa_percent = flt(lastday_dsa_percent)
	# 		item.mileage_amount=flt(item.mileage_rate) * flt(item.distance)
	# 		#item.amount = (flt(flt(item.dsa) * flt(item.dsa_percent) / 100) + flt(item.mileage_rate) * flt(item.distance))
	# 		item.amount = (flt((flt(item.days_allocated)*flt(dsa_per_day)) * flt(item.dsa_percent) / 100) + flt(item.mileage_rate) * flt(item.distance))
	# 		total_claim_days += flt(item.days_allocated)
	# 		item.base_amount = flt(item.amount)
	# 		total_travel_amount += flt(item.base_amount)
		
	# 	self.total_travel_amount = flt(total_travel_amount) + flt(self.extra_claim_amount)
	# 	self.total_claim_days = flt(total_claim_days)
	# 	diff = (flt(self.total_travel_amount) - flt(self.advance_amount))

	# 	if flt(diff) > 0:
	# 		self.total_travel_amount = flt(diff)
	# 		self.refundable_amount = 0
	# 	else:
	# 		self.refundable_amount = -1 * flt(diff)
	# 		self.total_travel_amount = 0

	def update_amounts(self):
		if self.grade:
			dsa_per_day=frappe.db.get_value("Employee Grade", self.grade, "dsa_per_day")
			#frappe.throw(dsa_per_day)
		# lastday_dsa_percent = flt(frappe.db.get_single_value("HR Settings", "return_day_dsa")) 
		total_travel_amount, diff = 0, 0
		
		total_claim_days = 0
		for item in self.get("items"):
			#item.total_dsa=dsa_per_day
			#frappe.msgprint(str(flt(item.days_allocated)))
			item.dsa = flt(item.total_dsa)
			# if flt(item.no_days)==0.0:
				# item.dsa_percent = flt(lastday_dsa_percent)
			# item.mileage_amount=flt(item.mileage_rate) * flt(item.distance)
			##item.amount = (flt(flt(item.dsa) * flt(item.dsa_percent) / 100) + flt(item.mileage_rate) * flt(item.distance))
			# item.amount = (flt((flt(item.no_days)*flt(dsa_per_day)) * flt(item.dsa_percent) / 100) + flt(item.mileage_rate) * flt(item.distance))
			total_claim_days += flt(item.no_days)
			# item.base_amount = flt(item.amount)
		# 	total_travel_amount += flt(item.base_amount)
		
		# self.total_travel_amount = flt(total_travel_amount) + flt(self.extra_claim_amount)
		self.total_claim_days = flt(total_claim_days)
		diff = (flt(self.total_travel_amount) - flt(self.advance_amount))

		if flt(diff) > 0:
			self.total_travel_amount = flt(diff)
			self.refundable_amount = 0
		else:
			self.refundable_amount = -1 * flt(diff)
			self.total_travel_amount = 0		

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
		self.post_payable_entry()
		if self.total_travel_amount > 0:
			self.post_payment_entry()
		# if self.refundable_amount > 0:
		# 	self.post_refund_entry()

	def post_payable_entry(self):
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

		advance_account = frappe.db.get_single_value("HR Accounts Settings",  "employee_advance_travel")
		if not advance_account:
			frappe.throw("Setup Advance to Employee (Travel) in HR Accounts Settings")

		# Payables
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1
		# je.title = "Travel Payable (" + self.employee_name + "  " + self.name + ")"
		je.title = "Travel Payment("+ self.name +")"
		je.voucher_type = "Journal Entry"
		je.naming_series = "Journal Voucher"
		# je.remark = 'Claim payment against : ' + self.name
		je.remark = 'Claim payment against : ' + self.name
		je.posting_date = self.posting_date
		je.branch = self.branch

		je.append("accounts", {
				"account": expense_account,
				"reference_type": "Bulk Travel Authorization",
				"reference_name": self.name,
				"cost_center": self.cost_center,
				"debit_in_account_currency": flt(self.total_travel_amount),
				"debit": flt(self.total_travel_amount),
			})

		if self.total_travel_amount > 0:
			je.append("accounts", {
					"account": payable_account,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"credit_in_account_currency": flt(self.total_travel_amount,2),
					"credit": flt(self.total_travel_amount,2),
					"party_type": "Employee",
					"party": self.employee, 
				})
		else:
			je.append("accounts", {
					"account": advance_account,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"credit_in_account_currency": flt(self.total_travel_amount),
					"credit": flt(self.total_travel_amount),
					"party_type": "Employee",
					"party": self.employee, 
				})

		if self.total_travel_amount > 0:
			je.append("accounts", {
				"account": advance_account,
				"party_type": "Employee",
				"party": self.employee,
				"reference_type": "Bulk Travel Authorization",
				"reference_name": self.name,
				"cost_center": cost_center,
				"credit_in_account_currency": flt(self.advance_amount),
				"credit": flt(self.advance_amount),
			})
		je.insert()
		je.submit()

	def post_payment_entry(self):
		payable_account = frappe.db.get_single_value("HR Accounts Settings", 'travel_claim_payable')
		expense_bank_account = get_bank_account(self.branch, self.company)
		if not expense_bank_account:
			frappe.throw("Setup Default Expense Bank Account in {}".format(frappe.get_desk_link("Branch", self.branch)))

		if flt(self.total_travel_amount) > 0:
			je = frappe.new_doc("Journal Entry")
			je.flags.ignore_permissions = 1
			# je.title = "Travel Payment(" + self.employee_name + "  " + self.name + ")"
			je.title = "Travel Payment("+ self.name +")"
			je.voucher_type = "Bank Entry"
			je.naming_series = "Bank Payment Voucher"
			je.remark = 'Claim payment against : ' + self.name
			je.posting_date = self.posting_date
			je.branch = self.branch
			je.append("accounts", {
					"account": payable_account,
					"party_type": "Employee",
					"party": self.employee,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"debit_in_account_currency": self.total_travel_amount,
					"debit": self.total_travel_amount,
				})

			je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": self.cost_center,
					"reference_type": "Bulk Travel Authorization",
					"reference_name": self.name,
					"credit_in_account_currency": flt(self.total_travel_amount),
					"credit": flt(self.total_travel_amount),
				})
			je.insert()		
		
	# def update_training_records(self, cancel=False):
	# 	emp_doc=frappe.get_doc("Employee", self.employee)
	# 	if cancel:
	# 		for child_d in emp_doc.get_all_children():
	# 			if child_d.doctype=='Training Records':
	# 				if child_d.from_date==self.from_date and child_d.to_date==self.to_date:
	# 					frappe.db.sql("delete from `tabTraining Records` where name = '{}'".format(child_d.name))
	
	# 	else:
	# 		emp_doc.append("train_record",{
	# 			"from_date": self.from_date,
	# 			"to_date": self.to_date,
	# 			"training_name": self.course_name,
	# 			"training_venue": self.training_venue,
	# 			"type_of_training": self.type_of_training,
	# 			"bond_period_from_date": self.bond_period_from_date,
	# 			"bond_period_to_date": self.bond_period_to_date

	# 		})
	# 		emp_doc.flags.ignore_permissions = 1
	# 		emp_doc.save()

	def update_training_event(self, cancel = False):
		if not cancel:
			if frappe.db.get_value("Training Event Employee", self.training_event_child_ref, "travel_authorization_id") in (None, ''):
				frappe.db.sql("""
					update `tabTraining Event Employee` set travel_authorization_id = '{}' where name = '{}'
					""".format(self.name, self.training_event_child_ref))
		else:
			if frappe.db.get_value("Training Event Employee", self.training_event_child_ref, "travel_authorization_id") == self.name:
				frappe.db.sql("""
					update `tabTraining Event Employee` set travel_authorization_id = NULL where name = '{}'
					""".format(self.training_event_child_ref))

	def validate_advance(self):
		self.advance_amount = 0 if not self.need_advance else self.advance_amount
		
		company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
		if self.currency == company_currency:
			self.exchange_rate = 1.0
			return
		
		advance_amt = 0
		if self.currency != company_currency:
			advance_amt = flt(self.base_advance_amount)
		else:
			advance_amt = flt(self.advance_amount)

		if flt(advance_amt) > flt(flt(self.estimated_amount) * 0.9):
			frappe.throw("Advance Amount cannot be greater than 90% of Total Estimated Amount")
		self.advance_journal = None if self.docstatus == 0 else self.advance_journal

	def set_travel_period(self):
		period = frappe.db.sql("""select min(`from_date`) as min_date, max(to_date) as max_date
				from `tabTravel Authorization Item` where parent = '{}' """.format(self.name), as_dict=True)
		if period:
			self.from_date 	= period[0].min_date
			self.to_date 	= period[0].max_date
	
	def assign_end_date(self):
		if self.items:
			self.end_date_auth = self.items[len(self.items) - 1].from_date 

	# def post_journal_entry(self):
	# 	company_currency = frappe.get_cached_value("Company", self.company, "default_currency")
	# 	advance_amt = 0
	# 	if self.currency != company_currency:
	# 		advance_amt = flt(self.base_advance_amount)
	# 	else:
	# 		advance_amt = flt(self.advance_amount)

	# 	if self.need_advance:
	# 		if flt(advance_amt) > 0:
	# 			cost_center = frappe.db.get_value("Employee", self.employee, "cost_center")
	# 			advance_account = frappe.db.get_single_value("HR Accounts Settings", "employee_advance_travel")
	# 			expense_bank_account = get_bank_account(self.branch, self.company)
	# 			# expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
	# 			if not cost_center:
	# 				frappe.throw("Setup Cost Center for employee in Employee Information")
	# 			if not expense_bank_account:
	# 				frappe.throw("Setup Default Expense Bank Account for your Branch")
	# 			if not advance_account:
	# 				frappe.throw("Setup Advance to Employee (Travel) in HR Accounts Settings")

	# 			voucher_type = 'Bank Entry'
	# 			naming_series = 'Bank Payment Voucher'

	# 			je = frappe.new_doc("Journal Entry")
	# 			je.flags.ignore_permissions = 1 
	# 			je.title = "TA Advance (" + self.employee_name + "  " + self.name + ")"
	# 			je.voucher_type = voucher_type
	# 			je.naming_series = naming_series
	# 			je.remark = 'Advance Payment against Travel Authorization: ' + self.name;
	# 			je.posting_date = self.posting_date
	# 			je.branch = self.branch
	
	# 			je.append("accounts", {
	# 				"account": advance_account,
	# 				"party_type": "Employee",
	# 				"party": self.employee,
	# 				"reference_type": self.doctype,
	# 				"reference_name": self.name,
	# 				"cost_center": cost_center,
	# 				"debit_in_account_currency": flt(advance_amt),
	# 				"debit": flt(advance_amt),
	# 				"is_advance": "Yes"
	# 			})

	# 			je.append("accounts", {
	# 				"account": expense_bank_account,
	# 				"cost_center": cost_center,
	# 				"credit_in_account_currency": flt(advance_amt),
	# 				"credit": flt(advance_amt),
	# 			})
				
	# 			je.insert(ignore_permissions=True)
	# 			self.db_set("journal_entry", je.name)

	def validate_travel_dates(self):
		for item in self.get("items"):
			if cint(item.halt):
				if not item.halt_at:
					frappe.throw(_("Row#{}: <b>Halt at</b> is mandatory").format(item.idx))
				elif not item.to_date:
					frappe.throw(_("Row#{0}: <b>To Date</b> is mandatory").format(item.idx),title="Invalid Date")
				elif item.from_date and item.to_date and (item.to_date < item.from_date):	
					frappe.throw(_("Row#{0}: <b>To Date</b> cannot be earlier to <b>From Date</b>").format(item.idx),title="Invalid Date")
			else:
				if not (item.travel_from and item.travel_to):
					frappe.throw(_("Row#{0}: <b>Travel From</b> and <b>Travel To</b> are mandatory").format(item.idx))
				item.to_date = item.from_date
			from_date = item.from_date
			to_date   = item.from_date if not item.to_date else item.to_date
			item.no_days   = date_diff(to_date, from_date) + 1

		# if self.items:
		# 	# check if the travel dates are already used in other travel authorization
		# 	tas = frappe.db.sql("""select t3.idx, t1.name, t2.from_date, t2.to_date
		# 			from 
		# 				`tabTravel Authorization` t1, 
		# 				`tabTravel Authorization Item` t2,
		# 				`tabTravel Authorization Item` t3
		# 			where t1.employee = "{employee}"
		# 			and t1.docstatus != 2
		# 			and t1.workflow_state !="Rejected"
		# 			and t1.name != "{travel_authorization}"
		# 			and t2.parent = t1.name
		# 			and t3.parent = "{travel_authorization}"
		# 			and (
		# 				(t2.from_date <= t3.to_date and t2.to_date >= t3.from_date)
		# 				or
		# 				(t3.from_date <= t2.to_date and t3.to_date >= t2.from_date)
		# 			)
		# 	""".format(travel_authorization = self.name, employee = self.employee), as_dict=True)
		# 	for t in tas:
		# 		frappe.throw("Row#{}: The dates in your current Travel Authorization have already been claimed in {} between {} and {}"\
		# 			.format(t.idx, frappe.get_desk_link("Travel Authorization", t.name), t.from_date, t.to_date))

		if self.items:
			# check if the travel dates are already used in other travel authorization
			tas = frappe.db.sql("""select t3.idx, t1.name, t2.from_date, t2.to_date
					from 
						`tabTravel Authorization` t1, 
						`tabTravel Authorization Item` t2,
						`tabTravel Authorization Item` t3
					where t1.employee = "{employee}"
					and t1.docstatus != 2
					and t1.name != "{travel_authorization}"
					and t2.parent = t1.name
					and t3.parent = "{travel_authorization}"
					and (
						(t2.from_date <= t3.to_date and t2.to_date >= t3.from_date)
						or
						(t3.from_date <= t2.to_date and t3.to_date >= t2.from_date)
					)
			""".format(travel_authorization = self.name, employee = self.employee), as_dict=True)
			for t in tas:
				frappe.throw("Row#{}: The dates in your current Travel Authorization have already been claimed in {} between {} and {}"\
					.format(t.idx, frappe.get_desk_link("Travel Authorization", t.name), t.from_date, t.to_date))

	def check_leave_applications(self):
		las = frappe.db.sql("""select t1.name from `tabLeave Application` t1 
				where t1.employee = "{employee}"
				and t1.docstatus != 2 and  case when t1.half_day = 1 then t1.from_date = t1.to_date end
				and exists(select 1
						from `tabTravel Authorization Item` t2
						where t2.parent = "{travel_authorization}"
						and (
							(t1.from_date <= t2.to_date and t1.to_date >= t2.from_date)
							or
							(t2.from_date <= t1.to_date and t2.to_date >= t1.from_date)
						)
				)
		""".format(travel_authorization = self.name, employee = self.employee), as_dict=True)
		for t in las:
			frappe.throw("The dates in your current travel authorization have been used in leave application {}".format(frappe.get_desk_link("Leave Application", t.name)))
	  
	@frappe.whitelist()
	def check_date_overlap(self):
		overlap = frappe.db.sql("""select t1.idx, 
				ifnull((select t2.idx from `tabTravel Authorization Item` t2
					where t2.parent = t1.parent
					and t2.name != t1.name
					and t1.from_date <= t2.to_date and t1.to_date >= t2.from_date
					limit 1),-1) overlap_idx
			from `tabTravel Authorization Item` t1
			where t1.parent = "{parent}"
			order by t1.from_date""".format(parent = self.name), as_dict=True)
			
		for d in overlap:
			if d.overlap_idx >= 0:
				frappe.throw(_("Row#{}: Dates are overlapping with dates in Row#{}").format(d.idx, d.overlap_idx))

	@frappe.whitelist()
	def set_dsa_per_day(self):
		if self.grade:
			self.dsa_per_day = frappe.db.get_value("Employee Grade", self.grade, "dsa_per_day")
		return self.dsa_per_day

	@frappe.whitelist()
	def set_estimate_amount(self):
		if not self.need_advance:
			return
 
		total_dsa = 0
		for i in self.items:
			if i.is_last_day == 0:
				total_dsa += flt(i.total_dsa)
		self.estimated_amount = total_dsa
		return total_dsa if total_dsa else 0.0

@frappe.whitelist()
def make_travel_claim(source_name, target_doc=None):
	def update_date(obj, target, source_parent):
		company_currency = frappe.get_cached_value("Company", obj.company, "default_currency")
		advance_amount = 0
		if obj.currency != company_currency:
			advance_amount = flt(obj.base_advance_amount)
		else:
			advance_amount = flt(obj.advance_amount)
		
		target.posting_date = nowdate()
		target.advance_amount = flt(advance_amount)
		target.supervisor = None

	def transfer_currency(obj, target, source_parent):
		if obj.halt:
			target.from_place = None
			target.to_place = None
		else:
			target.no_days = 1
			target.halt_at = None

		for item in source_parent.items:
			if source_parent.currency == "BTN":
				target.dsa = item.dsa
			else:
				target.base_dsa = item.dsa

		target.country=obj.country
		
	def adjust_last_date(source, target):
		dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
		for d in target.items:
			if d.is_last_day == 1:
				d.total_dsa = flt(d.total_dsa) * flt(dsa_percent)/100

	doc = get_mapped_doc("Travel Authorization", source_name, {
			"Travel Authorization": {
				"doctype": "Travel Claim",
				"field_map": {
					"name": "travel_authorization",
					"posting_date": "ta_date",
				},
				"postprocess": update_date,
				"validation": {"docstatus": ["=", 1]}
			},
			"Travel Authorization Item": {
				"doctype": "Travel Claim Item",
				"postprocess": transfer_currency,
			},
		}, target_doc, adjust_last_date)
	return doc

@frappe.whitelist()
def make_travel_adjustment(source_name, target_doc=None):
	res = frappe.db.sql("""select * from `tabTravel Authorization Item` where parent=%s order by idx asc
		""", (source_name), as_dict=True
	)

	def update_date(obj, target, source_parent):
		target.posting_date = nowdate()
		target.set(
			"travel_authorization_items",
			[d for d in res]
		)
	
	doc = get_mapped_doc("Travel Authorization", source_name, {
			"Travel Authorization": {
				"doctype": "Travel Adjustment",
				"field_map": {
					"name": "travel_authorization",
					"grade": "employee_grade",
				},
				"postprocess": update_date,
				"validation": {"docstatus": ["=", 1]},
			},
			"Travel Authorization Item": {
				"doctype": "Travel Adjustment Item",
			},
		}, 
		target_doc
	)
	
	return doc	

@frappe.whitelist()
def get_employee_dsa(country, grade):
    Doc = frappe.qb.DocType("Country")
    Child = frappe.qb.DocType("Country DSA Detail")
    
    query = (
        frappe.qb.from_(Doc)
        .join(Child).on(Child.parent == Doc.name)
        .where(
            (Doc.name == country) &
            (Child.grade == grade)
        )
        .select(
            Doc.currency,
            Child.dsa
        )
    )
    
    return query.run(as_dict=True)

@frappe.whitelist()
def get_approvers(doctype, txt, searchfield, start, page_len, filters):
    """
    Returns the expense approver for the selected employee
    """
    if not filters.get("employee"):
        frappe.throw(_("Please select an employee first"))

    employee = filters.get("employee")
    
    # Get expense approver from Employee
    expense_approver = frappe.db.get_value("Employee", employee, "reports_to")
    
    if not expense_approver:
        return []
    
    # Return user details if active
    return frappe.get_all("User",
        filters={
            "name": expense_approver,
            "enabled": 1
        },
        fields=["name as value", "full_name as description"],
        as_list=1
    )

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabTravel Authorization`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabTravel Authorization`.employee
				and `tabEmployee`.user_id = '{user}' and `tabTravel Authorization`.docstatus != 2)
		or
		(`tabTravel Authorization`.approver = '{user}' and `tabTravel Authorization`.workflow_state not in ('Draft','Rejected','Cancelled'))
	)""".format(user=user)

""" 
		exists(select 1
				from `tabEmployee`, `tabHas Role`
				where `tabEmployee`.user_id = `tabHas Role`.parent
				and `tabHas Role`.role = 'Travel Administrator'
				and (select region from `tabEmployee` where `tabEmployee`.name = `tabTravel Authorization`.employee limit 1) = (select region from `tabEmployee` where `tabEmployee`.user_id = '{user}' limit 1)
				and `tabEmployee`.user_id = '{user}')
		or
		 """