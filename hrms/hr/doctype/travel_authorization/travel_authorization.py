# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, nowdate, money_in_words, getdate
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
from frappe.utils.data import add_days, date_diff, today
from frappe.model.mapper import get_mapped_doc
from datetime import timedelta
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from erpnext.accounts.doctype.accounts_settings.accounts_settings import get_bank_account

class TravelAuthorization(Document):
	def validate(self):
		validate_workflow_states(self)
		self.validate_travel_last_day()
		self.assign_end_date()
		self.validate_advance()
		self.set_travel_period()
		self.validate_travel_dates(update=True)
		if self.training_event:
			self.update_training_event()
		if self.workflow_state != "Approved":
			notify_workflow_states(self)

	def on_update(self):
		self.validate_travel_dates()
		self.check_date_overlap()
		self.check_leave_applications()

	def on_submit(self):
		notify_workflow_states(self)
		self.validate_travel_dates(update=True)
		self.create_attendance()
		self.post_journal_entry()
		if self.travel_type=="Training":
			self.update_training_records()

	def validate_travel_last_day(self):
		if len(self.get("items")) > 1:
			self.items[-1].is_last_day = 1
	
	# def before_cancel(self):
	# 	self.update_training_records(cancel=True)
	# 	if self.advance_journal:
	# 		for t in frappe.get_all("Journal Entry", ["name"], {"name": self.advance_journal, "docstatus": ("<",2)}):
	# 			msg = '<b>Reference# : <a href="#Form/Journal Entry/{0}">{0}</a></b>'.format(t.name)
	# 			frappe.throw(_("Advance payment for this transaction needs to be cancelled first.<br>{0}").format(msg),title='<div style="color: red;">Not permitted</div>')
	# 	ta = frappe.db.sql("""
	# 		select name from `tabTravel Claim` where ta = '{}' and docstatus != 2
	# 	""".format(self.name))
	# 	if ta:
	# 		frappe.throw("""There is Travel Claim <a href="#Form/Travel%20Claim/{0}"><b>{0}</b></a> linked to this Travel Authorization""".format(ta[0][0]))
		
	def update_training_records(self, cancel=False):
		emp_doc=frappe.get_doc("Employee", self.employee)
		if cancel:
			for child_d in emp_doc.get_all_children():
				if child_d.doctype=='Training Records':
					if child_d.from_date==self.from_date and child_d.to_date==self.to_date:
						frappe.db.sql("delete from `tabTraining Records` where name = '{}'".format(child_d.name))
	
		else:
			emp_doc.append("train_record",{
				"from_date": self.from_date,
				"to_date": self.to_date,
				"training_name": self.course_name,
				"training_venue": self.training_venue,
				"type_of_training": self.type_of_training,
				"bond_period_from_date": self.bond_period_from_date,
				"bond_period_to_date": self.bond_period_to_date

			})
			emp_doc.save()

	def on_cancel(self):
		self.cancel_attendance()	
		if self.training_event:
			self.update_training_event(cancel=True)
		notify_workflow_states(self)

	def on_update_after_submit(self):
		if self.travel_claim:
			frappe.throw("Cannot change once claim is created")
		self.validate_travel_dates(update=True)
		self.check_date_overlap()
		self.check_leave_applications()
		self.db_set("end_date_auth", self.items[len(self.items) - 1].date)
		self.cancel_attendance()
		self.create_attendance()

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
		self.advance_amount     = 0 if not self.need_advance else self.advance_amount
		if flt(self.advance_amount) > flt(flt(self.estimated_amount) * 0.9):
			frappe.throw("Advance Amount cannot be greater than 90% of Total Estimated Amount")
		self.base_advance_amount  = 0 if not self.need_advance else self.base_advance_amount
		self.advance_journal    = None if self.docstatus == 0 else self.advance_journal

	def set_travel_period(self):
		period = frappe.db.sql("""select min(`from_date`) as min_date, max(to_date) as max_date
				from `tabTravel Authorization Item` where parent = '{}' """.format(self.name), as_dict=True)
		if period:
			self.from_date 	= period[0].min_date
			self.to_date 	= period[0].max_date

	def create_attendance(self):
		for row in self.items:
			from_date = getdate(row.from_date)
			to_date = getdate(row.to_date) if cint(row.halt) else getdate(row.from_date)
			noof_days = date_diff(to_date, from_date) + 1
			for a in range(noof_days):
				attendance_date = from_date + timedelta(days=a)
				al = frappe.db.sql("""select name from tabAttendance 
						where docstatus = 1 and employee = %s 
						and attendance_date = %s""", (self.employee, str(attendance_date)), as_dict=True)
				if al:
					doc = frappe.get_doc("Attendance", al[0].name)
					doc.cancel()
					
				#create attendance
				attendance = frappe.new_doc("Attendance")
				attendance.flags.ignore_permissions = 1
				attendance.employee = self.employee
				attendance.employee_name = self.employee_name 
				attendance.attendance_date = attendance_date
				attendance.status = "Tour"
				attendance.branch = self.branch
				attendance.company = frappe.db.get_value("Employee", self.employee, "company")
				attendance.reference_name = self.name
				attendance.submit()

	def cancel_attendance(self):
		if frappe.db.exists("Attendance", {"reference_name":self.name}):
			frappe.db.sql("delete from tabAttendance where reference_name = %s", (self.name))
	
	def assign_end_date(self):
		if self.items:
			self.end_date_auth = self.items[len(self.items) - 1].from_date 

	def post_journal_entry(self):
		if self.need_advance:
			if self.currency and flt(self.base_advance_amount) > 0:
				cost_center = frappe.db.get_value("Employee", self.employee, "cost_center")
				advance_account = frappe.db.get_single_value("HR Accounts Settings", "employee_advance_travel")
				expense_bank_account = get_bank_account(self.branch, self.company)
				# expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
				if not cost_center:
					frappe.throw("Setup Cost Center for employee in Employee Information")
				if not expense_bank_account:
					frappe.throw("Setup Default Expense Bank Account for your Branch")
				if not advance_account:
					frappe.throw("Setup Advance to Employee (Travel) in HR Accounts Settings")

				voucher_type = 'Bank Entry'
				naming_series = 'Bank Payment Voucher'

				je = frappe.new_doc("Journal Entry")
				je.flags.ignore_permissions = 1 
				je.title = "TA Advance (" + self.employee_name + "  " + self.name + ")"
				je.voucher_type = voucher_type
				je.naming_series = naming_series
				je.remark = 'Advance Payment against Travel Authorization: ' + self.name;
				je.posting_date = self.posting_date
				je.branch = self.branch
	
				je.append("accounts", {
					"account": advance_account,
					"party_type": "Employee",
					"party": self.employee,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"cost_center": cost_center,
					"debit_in_account_currency": flt(self.base_advance_amount),
					"debit": flt(self.base_advance_amount),
					"is_advance": "Yes"
				})

				je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": cost_center,
					"credit_in_account_currency": flt(self.base_advance_amount),
					"credit": flt(self.base_advance_amount),
				})
				
				je.insert(ignore_permissions=True)
				self.db_set("journal_entry", je.name)

	def validate_travel_dates(self, update=False):
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
			if update:
				frappe.db.set_value("Travel Authorization Item", item.name, "no_days", item.no_days)
		if self.items:
			# check if the travel dates are already used in other travel authorization
			tas = frappe.db.sql("""select t3.idx, t1.name, t2.from_date, t2.to_date
					from 
						`tabTravel Authorization` t1, 
						`tabTravel Authorization Item` t2,
						`tabTravel Authorization Item` t3
					where t1.employee = "{employee}"
					and t1.docstatus != 2
					and t1.workflow_state !="Rejected"
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
					.format(t.idx, frappe.get_desk_link("Travel Request", t.name), t.from_date, t.to_date))

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
		
		if len(self.items) > 1:
			first_day = self.items[0].from_date
			last_second_day = self.items[len(self.items) - 2].to_date
			total_days = date_diff(last_second_day, first_day) + 1
			self.estimated_amount = flt(total_days) * flt(self.dsa_per_day)
		else:
			self.estimated_amount = self.dsa_per_day
		return self.estimated_amount if self.currency == "BTN" else 0.0

@frappe.whitelist()
def make_travel_claim(source_name, target_doc=None):
	def update_date(obj, target, source_parent):
		target.posting_date = nowdate()
		target.supervisor = None

	def transfer_currency(obj, target, source_parent):
		if obj.halt:
			target.from_place = None
			target.to_place = None
		else:
			target.no_days = 1
			target.halt_at = None

		if source_parent.currency == "BTN":
			target.dsa = source_parent.dsa_per_day
		else:
			target.base_dsa = source_parent.dsa_per_day

		target.country=obj.country
		
	def adjust_last_date(source, target):
		dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
		for d in target.items:
			if d.is_last_day == 1:
				d.dsa = flt(d.dsa) * flt(dsa_percent)/100
				
	doc = get_mapped_doc("Travel Authorization", source_name, {
			"Travel Authorization": {
				"doctype": "Travel Claim",
				"field_map": {
					"name": "travel_authorization",
					"posting_date": "ta_date",
					"base_advance_amount": "advance_amount"
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
def get_exchange_rate(from_currency, to_currency, date=None):
	# Following line is replaced by subsequent code by SHIV on 2020/09/22
	#ex_rate = frappe.db.get_value("Currency Exchange", {"from_currency": from_currency, "to_currency": to_currency}, "exchange_rate")
	if not date or date == "" or date == " ":
		frappe.throw("Please select Currency Exchange Date.")
	
	ex_rate = frappe.db.sql("""select exchange_rate 
					from `tabCurrency Exchange`
					where from_currency = '{from_currency}'
					and to_currency = '{to_currency}'
					and `date` = '{data}'
					order by `date` desc
					limit 1
	""".format(from_currency=from_currency, to_currency=to_currency, data=date), as_dict=False)
 
	
	if not ex_rate:
		frappe.throw("No Exchange Rate defined in Currency Exchange for the date {}! Kindly contact your accounts section".format(date))
	else:
		return ex_rate[0][0]

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return
	if "HR Support" in user_roles:
		return """(
		exists(select 1
				from `tabAssign Branch`, `tabBranch Item`
				where `tabAssign Branch`.name = `tabBranch Item`.parent 
				and `tabBranch Item`.branch = `tabTravel Authorization`.branch
				and `tabAssign Branch`.user = '{user}')
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.branch = `tabTravel Authorization`.branch
				and `tabEmployee`.user_id = '{user}')
		)""".format(user=user)

	if "Accounts User" in user_roles or "GM" in user_roles:
		return """(
			exists(select 1
			from `tabAssign Branch`, `tabBranch Item`
			where `tabAssign Branch`.name = `tabBranch Item`.parent 
			and `tabBranch Item`.branch = `tabTravel Authorization`.branch
			and `tabAssign Branch`.user = '{user}')
		)""".format(user=user)
	
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