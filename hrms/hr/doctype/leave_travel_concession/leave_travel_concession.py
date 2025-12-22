# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, cint

class LeaveTravelConcession(Document):
	def validate(self):
		self.validate_duplicate()
		self.calculate_values()

	def on_submit(self):
		cc_amount = {}
		for a in self.items:
			cost_center = frappe.db.get_value("Employee", a.employee, "cost_center")
			cc = str(cost_center)
			if cc in cc_amount:
				cc_amount[cc] = cc_amount[cc] + a.amount
			else:
				cc_amount[cc] = a.amount
	
		self.post_journal_entry(cc_amount)

	def validate_duplicate(self):
		if not self.employee:
			doc = frappe.db.sql("select name from `tabLeave Travel Concession` where docstatus != 2 and fiscal_year = \'"+str(self.fiscal_year)+"\' and name != \'"+str(self.name)+"\'" )		
			if doc:
				frappe.throw("Cannot create multiple LTC for the same year")
		else:
			doc = frappe.db.sql("select b.employee from `tabLTC Details` b, `tabLeave Travel Concession` a where a.name = b.parent and b.employee = \'"+str(self.employee)+"\' and a.fiscal_year = \'"+str(self.fiscal_year)+"\' and a.docstatus not in (0,2)")
			if doc:
				frappe.throw("Cannot create multiple LTC for \'"+str(self.employee)+"\' for the same year")

	def calculate_values(self):
		if self.items:
			total = 0
			for a in self.items:
				total += flt(a.amount)
			self.total_amount = total
		else:
			frappe.throw("Cannot save without any employee records")

	def post_journal_entry(self, cc_amount):
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "LTC for " + self.branch + "(" + self.name + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'LTC payment against : ' + self.name;
		je.posting_date = self.posting_date
		je.branch = self.branch

		ltc_account = frappe.db.get_single_value("HR Accounts Settings", "ltc_account")
		if not ltc_account:
			frappe.throw("Setup LTC Account in HR Accounts Settings")

		expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		if not expense_bank_account:
			frappe.throw("Setup Expense Bank Account in Branch")

		for key in cc_amount.keys():
			values = key.split(":")
			je.append("accounts", {
					"account": ltc_account,
					"reference_type": "Leave Travel Concession",
					"reference_name": self.name,
					"cost_center": values[0],
					# "business_activity": values[1],
					"debit_in_account_currency": flt(cc_amount[key]),
					"debit": flt(cc_amount[key]),
				})
		
			je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": values[0],
					# "business_activity": values[1],
					"credit_in_account_currency": flt(cc_amount[key]),
					"credit": flt(cc_amount[key]),
				})

		je.insert()

		self.db_set("journal_entry", je.name)

	def on_cancel(self):
		jv = frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
		if jv and jv != 2:
			frappe.throw("Can not cancel LTC without canceling the corresponding journal entry " + str(self.journal_entry))
		else:
			self.db_set("journal_entry", None)


	@frappe.whitelist()
	def get_ltc_details(self):
		start, end = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"])
		
		if not self.employee:
			query = """
			select
				e.date_of_joining, 
				e.name as employee, 
				e.employee_name,
				e.employment_type, 
				e.designation, 
				e.branch,
				ifnull((
					select sd.amount
					from `tabSalary Structure` sst, `tabSalary Detail` sd
					where sst.employee = e.name
					and sst.eligible_for_ltc = 1
					and sst.from_date <= '{end_date}'
					and ifnull(sst.to_date,greatest(now(),'{end_date}')) >= '{end_date}'
					and sd.parent = sst.name
					and sd.salary_component = 'Basic Pay'
					order by ifnull(sst.to_date,greatest(now(),'{end_date}')) desc
					limit 1 
				),0) as amount,
				e.bank_name, e.bank_ac_no
			from `tabEmployee` e
			where e.date_of_joining <= '{start_date}'
			and ifnull(e.relieving_date,greatest(now(),'{end_date}')) >= '{end_date}'
			and exists(select 1
					from `tabSalary Structure` sst
					where sst.employee = e.name
					and sst.eligible_for_ltc = 1
					and ifnull(sst.to_date,greatest(now(),'{end_date}'))   >= '{end_date}'
					)
		""".format(start_date=str(start), end_date=str(end))
			query += " order by e.branch"
			entries = frappe.db.sql(query, as_dict=True)
		else:
			query = """
			select
				e.date_of_joining, 
				e.name as employee, 
				e.employee_name,
				e.employment_type,
				e.designation, 
				e.branch,
				ifnull((
					select sd.amount
					from `tabSalary Structure` sst, `tabSalary Detail` sd
					where sst.employee = e.name
					and sst.eligible_for_ltc = 1
					and sst.from_date <= '{end_date}'
					and ifnull(sst.to_date,greatest(now(),'{end_date}')) >= '{end_date}'
					and sd.parent = sst.name
					and sd.salary_component = 'Basic Pay'
					order by ifnull(sst.to_date,greatest(now(),'{end_date}')) desc
					limit 1 
				),0) as amount,
				e.bank_name, e.bank_ac_no
			from `tabEmployee` e
			where e.date_of_joining <= '{start_date}'
			and ifnull(e.relieving_date,greatest(now(),'{end_date}')) >= '{end_date}'
			and exists(select 1
					from `tabSalary Structure` sst
					where sst.employee = e.name
					and sst.eligible_for_ltc = 1
					and ifnull(sst.to_date,greatest(now(),'{end_date}'))   >= '{end_date}'
					)
			and e.employee = '{employee}'
		""".format(start_date=str(start), end_date=str(end), employee=str(self.employee))
			query += " order by e.branch"
			entries = frappe.db.sql(query, as_dict=True)

		self.set('items', [])

		for d in entries:
			d.basic_pay = d.amount
			if getdate(str(self.fiscal_year) + "-01-01") < getdate(d.date_of_joining) <  getdate(str(self.fiscal_year) + "-12-31"):
				if cint(str(d.date_of_joining)[8:10]) < 15:
					months = 12 - cint(str(d.date_of_joining)[5:7]) + 1
				else:
					months = 12 - cint(str(d.date_of_joining)[5:7])
				
				amount = d.amount
				if flt(d.amount) > 15000:
					amount = 15000
				d.amount = round(flt((flt(months)/12.0) * amount), 2)
			else:
				if flt(d.amount) > 15000:
					d.amount = 15000
			row = self.append('items', {})
			row.update(d)

