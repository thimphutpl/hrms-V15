# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, cint, date_diff,nowdate
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta
from hrms.hr.hr_custom_function import (get_salary_tax)


class LeaveTravelConcession(Document):
	def validate(self):
		self.validate_employee()
		self.validate_duplicate()
		self.calculate_values()

	def on_submit(self):
		
		for a in self.items:
			#cost_center = frappe.db.get_value("Employee", a.employee, ["cost_center"])
			tax=a.tax
			basic_pay=a.basic_pay
			net_amt=a.amount
			
				
		self.post_journal_entry(tax,basic_pay,net_amt)
	def validate_employee(self):
		if self.employee:
			employment_type = frappe.db.get_value("Employee",self.employee,"employment_status")
			joining_date = frappe.db.get_value("Employee",self.employee,"date_of_joining")
			working_days =date_diff(self.posting_date,joining_date)
			if employment_type == "Probation":
				frappe.throw("Employee who is in Probation Period is not eligible for LTC.")
			if working_days < 360 :
				frappe.throw("Employee who did not serve 1 year is not eligible for LTC")

	def validate_duplicate(self):
		# frappe.throw("hi")
		emp_list = ", ".join("'"+a.employee+"'" for a in self.items)
		doc = frappe.db.sql("""select 
						a.name 
					from 
						`tabLeave Travel Concession` a,
						`tabLTC Details` b 
					where
						a.name = b.parent
						and a.docstatus = 1 
						and a.fiscal_year = '{}' 
						and a.name != '{}'
						and b.employee = '{}'""".format(self.fiscal_year,self.name,self.employee),as_dict=True)		
		if doc:
			frappe.throw("Cannot create multiple LTC for the same year. One or more employees LTC already processed.")
	def calculate_values(self):
		if self.items:
			total = 0
			for a in self.items:
				total += flt(a.basic_pay) - flt(a.tax)
			self.total_amount = total
		else:
			frappe.throw("Cannot save without any employee records")

	def post_journal_entry(self,tax,basic_pay,net_amt):
	#def post_journal_entry(self):
		ltc_expense_account 	= frappe.db.get_single_value("HR Accounts Settings","ltc_account")
		ltc_payable_account 	= frappe.db.get_single_value("HR Accounts Settings","ltc_payable")
		tax_account 				= frappe.db.get_value("Company", self.company, "default_salary_tax_account")
		default_bank_account 		= frappe.db.get_value("Branch", self.branch, "expense_bank_account")
	

		if not ltc_expense_account:
			frappe.throw(
				"Ltc Expense Account is not set for {}. Please configure it in the Company.".format(
					frappe.get_desk_link("Company", self.company)
				),
				title="Missing Expense Account"
			)

		if not ltc_payable_account:
			frappe.throw(
				"Ltc Payable Account is not set for {}. Please configure it in the Company.".format(
					frappe.get_desk_link("Company", self.company)
				),
				title="Missing Payable Account"
			)

		if not tax_account:
			frappe.throw(
				"Default Salary Tax Account is not set for {}. Please configure it in the Company.".format(
					frappe.get_desk_link("Company", self.company)
				),
				title="Missing Tax Account"
			)

		if not default_bank_account:
			frappe.throw(
				"Default Expense Bank Account is not set for {}. Please configure it in the Branch.".format(
					frappe.get_desk_link("Branch", self.branch)
				),
				title="Missing Bank Account"
			)

		posting = frappe._dict()
		
		# Payables
		posting.setdefault("to_payables", []).append({
			"account" 					: ltc_expense_account,
			"debit_in_account_currency"	: basic_pay,
			# "cost_center"    			: self.cost_center,
			"party_check"			 	: 0,
			"reference_type"			: self.doctype,
			"reference_name"			: self.name,
		})
		if flt(tax) > 0:
			posting.setdefault("to_payables", []).append({
				"account" 					: tax_account,
				"credit_in_account_currency": flt(tax),
				# "cost_center"    			: self.cost_center,
				"party_check"				: 0,
				"reference_type"			: self.doctype,
				"reference_name"			: self.name,
			})
		posting.setdefault("to_payables", []).append({
			"account" 						: ltc_payable_account,
			"credit_in_account_currency"	: net_amt,
			# "cost_center"    				: self.cost_center,
			"party_check"					: 1,
			"party_type"					: "Employee",
			"party"							: self.employee,
			"reference_type"				: self.doctype,
			"reference_name"				: self.name,
		})

		# To Bank
		posting.setdefault("to_bank", []).append({
			"account"       				: ltc_payable_account,
			"debit_in_account_currency"		: net_amt,
			# "cost_center"   				: self.cost_center,
			"party_check"					: 1,
			"party_type"					: "Employee",
			"party"							: self.employee,
			"reference_type"				: self.doctype,
			"reference_name"				: self.name,
		})
		posting.setdefault("to_bank", []).append({
			"account"       				: default_bank_account,
			"credit_in_account_currency"	: net_amt,
			# "cost_center"   				: self.cost_center,
			"party_check"   				: 0,
			"reference_type"				: self.doctype,
			"reference_name"				: self.name,
		})

		jv_name, v_title = None, ""
		for i in posting:
			if i == "to_payables":
				title         = "To Payables"
				voucher_type  = "Journal Entry"
				naming_series = "Journal Voucher"
			else:
				title         = "To Bank"
				voucher_type  = "Bank Entry"
				naming_series = "Bank Payment Voucher"

			doc = frappe.get_doc({
					"doctype"			: "Journal Entry",
					"voucher_type"		: voucher_type,
					"naming_series"		: naming_series,
					"title"				: title,
					"remark"			: title,
					"posting_date"		: nowdate(),                     
					"company"			: self.company,
					"accounts"			: posting[i],
					"branch"			: self.branch,
				})

			
			doc.flags.ignore_permissions = 1 
			doc.insert()
			if i == "to_payables":
				doc.submit()
			else:
				pass
				#self.db_set("journal_entry", doc.name)
				#self.db_set("journal_entry_status", "Forwarded to accounts for processing payment on ")

		

	def on_cancel(self):
		jv_doc = frappe.get_doc("Journal Entry", self.journal_entry)
		# jv = frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
		if jv_doc and jv_doc.docstatus != 2:
			frappe.throw("Can not cancel LTC without canceling the corresponding journal entry " + str(self.journal_entry))
		else:
			self.db_set("journal_entry", None)


	@frappe.whitelist()
	def get_ltc_details(self):
		start, end = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"])
		employee_filter = ""
		if self.employee:
			employee_filter = " and b.employee = '{}' ".format(self.employee)
		entries = frappe.db.sql("""
					select 
						e.date_of_joining, 
						b.employee, 
						b.employee_name, 
						b.branch, 
						a.amount, 
						e.bank_name, 
						e.bank_ac_no  
					from 
						`tabSalary Detail` a, 
						`tabSalary Structure` b, 
						`tabEmployee` e 
					where 
						a.parent = b.name 
						and b.employee = e.name 
						and a.salary_component = 'Basic Salary' 
						and (b.is_active = 'Yes' or e.relieving_date between \'"+str(start)+"\' and \'"+str(end)+"\')
						and b.eligible_for_ltc = 1
						""" + employee_filter + """
					order by b.branch """, as_dict=True)
		self.set('items', [])
		for d in entries:
			datediff = date_diff(nowdate(), d.date_of_joining)
			# frappe.throw(str(datediff))
			if datediff < 366:
				frappe.throw("your not engiable for ltc")
				

			else:
				
				d.tax = get_salary_tax(d.amount)
				d.basic_pay=d.amount
				d.amount=d.amount-d.tax
				
			row = self.append('items', {})
			
			row.update(d)


