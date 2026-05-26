# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cint,get_last_day
from calendar import monthrange
import pymysql
from erpnext.custom_utils import check_budget_available, get_branch_cc

class ProcessMRPayment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.projects.doctype.mr_payment_item.mr_payment_item import MRPaymentItem
		from frappe.types import DF

		amended_from: DF.Link | None
		branch: DF.Link
		cost_center: DF.Link
		deduction: DF.Currency
		employee_type: DF.Literal["", "Muster Roll Employee", "Operator", "Open Air Prisoner", "DFG", "GFG"]
		fiscal_year: DF.Link | None
		from_date: DF.Date | None
		gratuity_amount: DF.Currency
		items: DF.Table[MRPaymentItem]
		month: DF.Literal["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
		monthyear: DF.Literal["201701", "201702", "201703", "201704", "201705", "201706", "201707", "201708", "201709", "201710", "201711", "201712", "201801", "201802", "201803", "201804", "201805", "201806", "201807", "201808", "201809", "201810", "201811", "201812", "201901", "201902", "201903", "201904", "201905", "201906", "201907", "201908", "201909", "201910", "201911", "201912", "202001", "202002", "202003", "202004", "202005", "202006", "202007", "202008", "202009", "202010", "202011", "202012", "202101", "202102", "202103", "202104", "202105", "202106", "202107", "202108", "202109", "202110", "202111", "202112", "202201", "202202", "202203", "202204", "202205", "202206", "202207", "202208", "202209", "202210", "202211", "202212", "202301", "202302", "202303", "202304", "202305", "202306", "202307", "202308", "202309", "202310", "202311", "202312", "202401", "202402", "202403", "202404", "202405", "202406", "202407", "202408", "202409", "202410", "202411", "202412", "202501", "202502", "202503", "202504", "202505", "202506", "202507", "202508", "202509", "202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605", "202606", "202607", "202608", "202609", "202610", "202611", "202612", "202701", "202702", "202703", "202704", "202705", "202706", "202707", "202708", "202709", "202710", "202711", "202712"]
		ot_amount: DF.Currency
		payment_jv: DF.Data | None
		posting_date: DF.Date
		project: DF.Link | None
		to_date: DF.Date | None
		total_amount_payable: DF.Currency
		total_health_amount: DF.Currency
		total_overall_amount: DF.Currency
		wages_amount: DF.Currency
	# end: auto-generated types
	def validate(self):
		self.validate_duplicate_entry()
		# Setting `monthyear`		

	def before_save(self):	
		month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].index(self.month) + 1
		month = str(month) if cint(month) > 9 else str("0" + str(month))
		self.monthyear = str(self.fiscal_year)+str(month)
		total_days = monthrange(cint(self.fiscal_year), cint(month))[1]	
		if self.items:
			for a in self.items:
				self.duplicate_entry_check(a.employee, a.employee_type, a.idx)
				a.fiscal_year = self.fiscal_year
				a.month = self.month

				# if a.employee_type == "Operator":
				# 	#frappe.throw(str(a.employee))
				# 	salary = frappe.db.get_value("Operator", a.employee, "salary")
				# 	if salary:
				# 		if flt(a.total_wage) > flt(salary):
				# 			a.total_wage = flt(salary)
				# 		if flt(total_days) == round(flt(a.number_of_days), 2):
				# 			a.total_wage = flt(salary)
				# elif a.employee_type == 'DFG AND GFG':
				# 	#frappe.throw(a.employee_type)
				# 	salary = frappe.db.get_value("DFG AND GFG", {'id_card':a.id_card}, "salary")
				# 	#frappe.throw(str(salary))
				# 	if salary:
				# 		#frappe.throw(str(salary))
						
				# 		if flt(a.total_wage) > flt(salary):
							
				# 			a.total_wage = flt(salary)
				# 			frappe.throw(a.total_wage)
				# 		if flt(total_days) == round(flt(a.number_of_days), 2):
							
				# 			a.total_wage = flt(salary)
				# 		cond_days = total_days-2

				# 		if cond_days > a.number_of_days:
				# 			a.total_wage = a.daily_rate * a.number_of_days 
				# 		if total_days == 31 and a.number_of_days >= 28:
				# 			a.total_wage = flt(salary)

				# elif round(flt(a.number_of_days), 2) >= 28 and self.employee_type !="Muster Roll Employee":
				# 	pass
				# 	# salary = frappe.db.get_value("Employee", a.employee, "salary")
				# 	# if salary:
				# 	# 	a.total_wage = flt(salary)
				# elif a.employee_type == 'Open Air Prisoner':					
				# 	salary = flt(total_days) * flt(a.daily_rate)
				# 	if flt(a.total_wage) > flt(salary):
				# 		a.total_wage = flt(salary)
				# 	if flt(total_days) == round(flt(a.number_of_days), 2):
				# 		a.total_wage = flt(salary)

				# a.total_wage = round(a.total_wage)
				# a.total_ot_amount = a.total_ot_amount
				# a.gratuity_amount = round(a.gratuity_amount)

				# if a.employee_type == "Open Air Prisoner":
				# 	gratuity_percent = frappe.db.get_single_value("HR Settings", "gratuity_percent")
				# 	if gratuity_percent:
				# 		a.total_gratuity = flt(gratuity_percent) / 100 * flt(a.total_wage)
				# 		a.wage_payable = flt(a.total_wage) - flt(a.gratuity_amount)
				# a.total_amount = flt(a.total_ot_amount) + flt(a.total_wage)

			# total_ot = sum(flt(a.total_ot_amount) for a in self.items)
			# total_wage = sum(flt(a.total_wage) for a in self.items)
			# total_gratuity = sum(flt(a.gratuity_amount) for a in self.items)
			# total = total_ot + total_wage
			# self.wages_amount = flt(total_wage)
			# self.ot_amount = flt(total_ot)
			# self.total_overall_amount = flt(total)
			# self.gratuity_amount = flt(total_gratuity)

		
	def on_submit(self):
		#frappe.throw("hi")
		# self.check_budget()
		self.post_journal_entry()

	def before_cancel(self):
		self.flags.ignore_links = True
		cl_status = frappe.db.get_value("Journal Entry", self.payment_jv, "docstatus")
		if cl_status and cl_status != 2:
			frappe.throw("You need to cancel the journal entry related to this payment first!")
		
		self.db_set('payment_jv', "")
		self.db_set('journal_entry',"")
		
	def check_budget(self):
				
		budget_error= []
		expense_bank_account, ot_account, wage_account, gratuity_account = self.prepare_gls()
		wages_amount = self.wages_amount
		if self.employee_type == 'Open Air Prisoner' and self.gratuity_amount:
			wages_amount = wages_amount - flt(self.gratuity_amount)
			error = check_budget_available(self.cost_center, ot_account, self.posting_date, self.ot_amount, False)
			if error:
				budget_error.append(error)
				errors= check_budget_available(self.cost_center, wage_account, self.posting_date, wages_amount, throw_error = False)
				if errors:
					budget_error.append(errors)
					if budget_error:
						for e in budget_error:
							frappe.msgprint(str(e))
							frappe.throw("", title="Insufficient Budget")


	def duplicate_entry_check(self, employee, employee_type, idx):
			pl = frappe.db.sql("""
							select
									i.name,
									i.parent,
									i.docstatus,
									i.person_name,
									i.employee
							from `tabMR Payment Item` i, `tabProcess MR Payment` m
							where i.employee = '{0}'
							and i.employee_type = '{1}'
							and i.fiscal_year = '{2}'
							and i.month = '{3}'
							and m.docstatus in (0,1)
							and i.parent != '{4}'
			and i.parent = m.name
			and m.cost_center = '{5}'
					""".format(employee, employee_type, self.fiscal_year, self.month, self.name, self.cost_center), as_dict=1)

			for l in pl:
					msg = 'Payment already processed for `{2}({3})`<br>RowId#{1}: Reference# <a href="#Form/Process MR Payment/{0}">{0}</a>'.format(l.parent, idx, l.person_name, l.employee)
					frappe.throw(_("{0}").format(msg), title="Duplicate Record Found")                        
				
	#Populate Budget Accounts with Expense and Fixed Asset Accounts
	def load_employee(self):
		# if self.employee_type == "Operator":
		# 	query = "select 'Operator' as employee_type, name as employee, person_name, id_card, rate_per_day as daily_rate, rate_per_hour as hourly_rate from `tabOperator` where	status = 'Active'"
		
		# elif self.employee_type == "DFG":
		# 	query = "select 'DFG' as employee_type, name as employee, person_name, id_card, rate_per_day as daily_rate, rate_per_hour as hourly_rate from `tabDFG` where status = 'Active'"

		# elif self.employee_type == "Open Air Prisoner":
		# 				query = "select 'Open Air Prisoner' as employee_type, name as employee, person_name, id_card, rate_per_day as daily_rate, rate_per_hour as hourly_rate, gratuity_fund as graduity from `tabOpen Air Prisoner` where status = 'Active'"

		if self.employee_type == "Muster Roll Employee":
			frappe.throw("hi")
			query = "select 'Muster Roll Employee' as employee_type, r.type,r.name as employee, r.person_name, r.id_card, m.rate_per_day as daily_rate, m.rate_per_hour as hourly_rate from `tabMuster Roll Employee` r, tabMusterroll m where r.status = 'Active' and r.name=m.parent order by m.rate_per_day"
		else:
			frappe.throw("Select employee record first!")
	
		if not self.branch:
			frappe.throw("Set Branch before loading employee data")
		else:
			query += " and branch = \'" + str(self.branch) + "\'"	
			
		entries = frappe.db.sql(query, as_dict=True)
		if not entries:
			frappe.msgprint("No Attendance and Overtime Record Found")

		self.set('items', [])

		for d in entries:
			row = self.append('items', {})
			row.update(d)

	def validate_duplicate_entry(self):
		
		data = []
		for a in self.items:
			
			if a.employee not in data:
				data.append(a.employee)
				#frappe.throw(str(data))
			else:
				frappe.throw("Duplicate Employee entry {} at #Row. {}".format(a.employee, a.idx))

	def post_journal_entry(self):
		expense_bank_account,je_expense_bank_account,mu_account, lp_account,je_mu_account,je_lp_account = self.prepare_gls()
		# expense_bank_account=frappe.db.get_value("Cost Center",self.cost_center,"expense_account")
		if not expense_bank_account:
			frappe.throw("Set Expense Account In Cost Center for '{}'".format(self.cost_center))
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "Payment for " + self.employee_type  + " (" + self.branch + ")" + "(" + self.month + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'Payment against : ' + self.name
		je.posting_date = self.posting_date
		je.branch = self.branch
		total_amount_mu = self.total_overall_amount
		total_amount_lp = self.gross_loading_amount
					

		je.append("accounts", {
				"account": expense_bank_account,
				"cost_center": self.cost_center,
				"credit_in_account_currency": flt(self.total_amount),
				"credit": flt(self.total_amount),
			})
	
		if self.total_overall_amount:	
			je.append("accounts", {
					"account": je_expense_bank_account,
					"reference_type": "Process MR Payment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"debit_in_account_currency": flt(self.total_amount),
					"debit": flt(self.total_amount),
				})

		# if self.gross_loading_amount:
		# 	je.append("accounts", {
		# 			"account": lp_account,
		# 			"reference_type": "Process MR Payment",
		# 			"reference_name": self.name,
		# 			"cost_center": self.cost_center,
		# 			"debit_in_account_currency": flt(total_amount_lp),
		# 			"debit": flt(total_amount_lp),
		# 		})

		je.insert()
		self.db_set("payment_jv", je.name)


		je_journal = frappe.new_doc("Journal Entry")
		je_journal.flags.ignore_permissions = 1 
		je_journal.title = "Payable " + self.employee_type + " (" + self.branch + ")" + "(" + self.month + ")"
		je_journal.voucher_type = 'Journal Entry'
		je_journal.naming_series ='Journal Voucher'
		je_journal.remark = 'loading and unloading payable : ' + self.name
		je_journal.posting_date = self.posting_date
		je_journal.branch = self.branch

		# Debit entry for expense_bank_account (opposite of bank entry)
		je_journal.append("accounts", {
			"account": je_expense_bank_account,
			"cost_center": self.cost_center,
			"credit_in_account_currency": flt(self.total_amount),
			"credit": flt(self.total_amount),
		})

		# Credit entries for MU and LP accounts
		if self.total_overall_amount:	
			je_journal.append("accounts", {
				"account": mu_account,
				"reference_type": "Process MR Payment",
				"reference_name": self.name,
				"cost_center": self.cost_center,
				"debit_in_account_currency": flt(total_amount_mu),
				"debit": flt(total_amount_mu),
			})

		if self.gross_loading_amount:
			je_journal.append("accounts", {
				"account": lp_account,
				"reference_type": "Process MR Payment",
				"reference_name": self.name,
				"cost_center": self.cost_center,
				"debit_in_account_currency": flt(total_amount_lp),
				"debit": flt(total_amount_lp),
			})

		je_journal.insert()
		je_journal.submit()

		# Optionally store both references
		#self.db_set("payment_jv", je_bank.name)
		self.db_set("journal_entry", je_journal.name)  # Add this field to your doctype if needed


		
		


	def prepare_gls(self):
		gratuity_account = None
		expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		je_expense_bank_account = frappe.db.get_single_value("HR Accounts Settings","muster_roll_payable_account")
		if not expense_bank_account:
			frappe.throw("Setup Default Expense Bank Account for your Branch")

		# Initialize variables
		ot_account = None
		wage_account = None

		if self.employee_type == "Muster Roll Employee":
			account = frappe.get_doc("Muster Roll Type", "muster roll","account")
			mu_account=account.account
			if not mu_account:
				frappe.throw("Setup MR Overtime Account")
			account1 = frappe.get_doc("Muster Roll Type", "Unloading and loading","account")
			lp_account=account1.account
			if not lp_account:
				frappe.throw("Setup lp Account")

			je_mu_account=frappe.db.get_single_value("HR Accounts Settings","mr_wages_account")
			if not je_mu_account:
				frappe.throw("Setup MR Wages Account in HR Accounts Settings")

			je_lp_account=je_mu_account=frappe.db.get_single_value("HR Accounts Settings","mr_overtime_account")
			if not je_lp_account:
				frappe.throw("Setup MR Overtime Account in HR Accounts Settings")




		
		else:
			frappe.throw("Invalid Employee Type")

		return expense_bank_account,je_expense_bank_account,mu_account, lp_account,je_mu_account,je_mu_account
	
def update_mr_rates(employee_type, employee, cost_center, from_date, to_date):
	# Updating wage rate
	rates = frappe.db.sql("""
		select
						greatest(ifnull(from_date,'{from_date}'),'{from_date}') as from_date, 
			least(ifnull(to_date,'{to_date}'),'{to_date}') as to_date, 
			rate_per_day,
			rate_per_hour_normal
		from `tabMusterroll`
		where parent = '{employee}'
		and '{year_month}' between date_format(ifnull(from_date,'{from_date}'),'%Y%m') and date_format(ifnull(to_date,'{to_date}'),'%Y%m')
	""".format(
		employee=employee,
		year_month=str(to_date)[:4]+str(to_date)[5:7],
		from_date=from_date,
		to_date=to_date
	),
	as_dict=True)
#	frappe.msgprint('{0}'.format(rates))
	for r in rates:
		frappe.db.sql("""
			update `tabAttendance Others`
			set rate_per_day = {rate_per_day}
			where employee_type = '{employee_type}'
			and employee = '{employee}'
			and `date` between '{from_date}' and '{to_date}'
			and status in ('Present', 'Half Day')
			and docstatus = 1 
		""".format(
			rate_per_day=r.rate_per_day,
			employee_type=employee_type,
			employee=employee,
			from_date=r.from_date,
			to_date=r.to_date
		))

		frappe.db.sql("""
			update `tabOvertime Entry`
			set rate_per_hour = {rate_per_hour}
			where employee_type = '{employee_type}'
			and number = '{employee}'
			and `date` between '{from_date}' and '{to_date}'
			and docstatus = 1 
		""".format(
			rate_per_hour=r.rate_per_hour_normal,
			employee_type=employee_type,
			employee=employee,
			from_date=r.from_date,
			to_date=r.to_date
		))

	frappe.db.commit()

@frappe.whitelist()
def get_records(employee_type, fiscal_year, fiscal_month, from_date, to_date, cost_center, branch, dn):	
	
	
	month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"].index(fiscal_month) + 1
	month = str(month) if cint(month) > 9 else str("0" + str(month))
	# if employee_type == 'DFG' or employee_type =='GFG':
		
	# 	if employee_type=='DFG':
	# 		employee_category='DFG'
	# 	elif employee_type=='GFG':
	# 		employee_category='GFG'
	# 	employee_type = 'DFG AND GFG'
	
	if employee_type=='Muster Roll Employee':
		employee_type='Muster Roll Employee'
		employee_category='NULL'
	# elif employee_type=='Operator':
	# 	employee_type='Operator'
	# 	employee_category='NULL'
	
	# elif employee_type=='Open Air Prisoner':
	# 	employee_type='Open Air Prisoner'
	# 	employee_category='NULL'
	# # frappe.throw(str(employee_type))

	total_days = monthrange(cint(fiscal_year), cint(month))[1]
	from_date = str(fiscal_year) + '-' + str(month) + '-' + str('01')
	to_date   = str(fiscal_year) + '-' + str(month) + '-' + str(total_days)

	data    = []
	master  = frappe._dict()
	#qfrappe.throw(str(to_date))
	emp_list = frappe.db.sql("""
								select
										name,
										person_name,
										id_card,
										rate_per_day,
										type,
										rate_per_hour,
					status,
					designation,
					bank,
					account_no,
										salary
								from `tab{employee_type}` as e
								where not exists(
										select 1
										from `tabMR Payment Item` i, `tabProcess MR Payment` m
										where m.fiscal_year = '{fiscal_year}'
					and m.month = '{fiscal_month}'
					and m.docstatus < 2
					and m.cost_center = '{cost_center}'
					and m.name != '{dn}'
					and i.parent = m.name
					and i.employee = e.name
					and i.employee_type = '{employee_type}'
								)
				and (
					exists(
					select 1
					from `tabAttendance Others`
								where employee_type = '{employee_type}'
					and employee = e.name and (emp_cat='{employee_category}' or emp_cat is NULL or emp_cat='')
										and date between '{from_date}' and '{to_date}'
										and cost_center = '{cost_center}'
										and status in ('Present', 'Half Day')
										and docstatus = 1
					)
					or
					exists(
					select 1
					from `tabOvertime Entry`
										where employee_type = '{employee_type}'
					and number = e.name
										and date between '{from_date}' and '{to_date}'
										and cost_center = '{cost_center}'
										and docstatus = 1
					)

				)
		""".format(
				employee_type=employee_type,
				fiscal_year=fiscal_year,
				fiscal_month=fiscal_month,
				dn=dn,
				cost_center=cost_center,
			from_date = from_date,
			to_date = to_date,
			employee_category=employee_category
		),as_dict=True)	
	


	for e in emp_list:
		is_lifer=0
		#frappe.throw(str(e.id_card))
		salary=0
		# if employee_type == 'DFG AND GFG':
		# 	pay_details=get_pay_details_dfg_gfg_opa_opt(e.name,employee_type)
		# 	#frappe.throw(str(pay_details))
		# 	rate_per_day 		 = flt(pay_details[0]['rate_per_day'])
		# 	rate_per_hour_normal = flt(pay_details[0]['rate_per_hour'])
		# 	salary=flt(pay_details[0]['salary'])
		
		# elif employee_type=='Operator':
		# 	pay_details=get_pay_details_dfg_gfg_opa_opt(e.name,employee_type)
		# 	rate_per_day=flt(pay_details[0]['rate_per_day'])
		# 	rate_per_hour_normal=flt(pay_details[0]['rate_per_hour'])
		# 	salary=flt(pay_details[0]['salary'])
		# 	#frappe.throw(str(pay_details))
		# elif employee_type=='Open Air Prisoner':
		# 	pay_details=get_pay_opa(e.name,employee_type)
		# 	rate_per_day=flt(pay_details[0]['rate_per_day'])
		# 	rate_per_hour_normal=flt(pay_details[0]['rate_per_hour'])
		# 	is_lifer=flt(pay_details[0]['is_lifer'])
		# 	salary=flt(pay_details[0]['salary'])

		# else:
		pay_details=get_pay_details(e.name)
		if not pay_details:
			# Log a warning and skip processing for this employee
			frappe.throw(f"No pay details found for Employee: {e.name} for Fiscal Year: {fiscal_year}, Month: {month}")
			continue			
		rate_per_day = flt(pay_details[e.name]['rate_per_day'])		
		rate_per_hour_normal = flt(pay_details[e.name]['rate_per_hour_normal'])
		

		master.setdefault(e.name, frappe._dict({
			"employee_type": employee_type,
			"employee": e.name,
			"type":e.type,
			"person_name": e.person_name,
			"id_card": e.id_card,
			"rate_per_day": rate_per_day,
			"rate_per_hour": rate_per_hour_normal,
			"designation" : e.designation,
			"account_no" : e.account_no,
			"bank" : e.bank,
			"salary":salary,
			"is_lifer":is_lifer
		}))
		# if employee_type == "Muster Roll Employee":
		# 	update_mr_rates(employee_type, e.name, cost_center, from_date, to_date)
		# if employee_type in ('Operator', 'Open Air Prisoner', 'DFG AND GFG'):
		
		# 	frappe.db.sql("""
		# 				update `tabAttendance Others`
		# 				set rate_per_day = {rate_per_day}
		# 				where employee_type = '{employee_type}'
		# 				and employee = '{employee}'
		# 				and status in ('Present', 'Half Day')
		# 				and docstatus = 1 
		# 		""".format(
		# 				rate_per_day=flt(rate_per_day),
		# 				employee_type=employee_type,
		# 				employee=e.name,
		# 		))

		# 	frappe.db.sql("""
		# 		update `tabOvertime Entry`
		# 		set rate_per_hour = {rate_per_hour}
		# 		where employee_type = '{employee_type}'
		# 		and number = '{employee}'
		# 		and docstatus = 1 
		# 	""".format(
		# 			rate_per_hour=flt(e.rate_per_hour),
		# 			employee_type=employee_type,
		# 			employee=e.name,
		# 	))

		# frappe.db.commit()  

	#	
	rest_list = frappe.db.sql("""
								select employee,
										sum(number_of_days)     as number_of_days,
										sum(number_of_hours)    as number_of_hours,
										sum(total_wage)         as total_wage,
										sum(total_ot)           as total_ot,
										{4} as noof_days_in_month
								from (
										select distinct
												employee,
						date,
												1                       as number_of_days,
												0                       as number_of_hours,
												ifnull(rate_per_day,0)  as total_wage,
												0                       as total_ot
										from `tabAttendance Others`
										where employee_type = '{0}'
										and date between '{1}' and '{2}'
										and cost_center = '{3}'
										and status = 'Present'
										and docstatus = 1
										UNION ALL
					select distinct
												employee,
												date,
												.5                     as number_of_days,
												0                       as number_of_hours,
												ifnull(rate_per_day,0)  as total_wage,
												0                       as total_ot
										from `tabAttendance Others`
										where employee_type = '{0}'
										and date between '{1}' and '{2}'
										and cost_center = '{3}'
										and status = 'Half Day'
										and docstatus = 1
					UNION ALL
										select distinct
												number                  as employee,
						date,
												0                       as number_of_days,
												ifnull(number_of_hours,0) as number_of_hours,
												0                       as total_wage,
												ifnull(number_of_hours,0)*ifnull(rate_per_hour,0) as total_ot
										from `tabOvertime Entry`
										where employee_type = '{0}'
										and date between '{1}' and '{2}'
										and cost_center = '{3}'
										and docstatus = 1
								) as abc
								group by employee
	""".format(employee_type, from_date, to_date, cost_center, total_days), as_dict=True)


	for r in rest_list:
		gratuity = 0.0
		#frappe.throw(str(r.gratuity))
		#gratuity_percent = frappe.db.get_single_value("HR Settings", "gratuity_percent")
		gratuity_percent=1
		if master.get(r.employee): #and (flt(r.total_wage)+flt(r.total_ot)):
			#frappe.throw(str(r.type))
			#frappe.throw(str(mr['type']))
			#r.employee_type = r.type
			#frappe.msgprint(str(master[r.employee]['type']))
			r.gratuity = flt(gratuity_percent)/100 * flt(r.total_wage)
			master[r.employee].update(r)
			
			data.append(master[r.employee])
				   
	if data:
		#frappe.throw(str(data))
		return data
	else:
		frappe.throw(_("No data found!"),title="No Data Found!")



@frappe.whitelist()
def get_is_lifer_status(employee):	
	"""
	Get 'is_lifer' status for a given employee.
	"""	
	is_lifer = frappe.db.get_value("Open Air Prisoner", {"name": employee}, "is_lifer")
	if is_lifer is not None:
		return {"is_lifer": is_lifer}
	else:
		return {"error": "No data found for this employee."}


def get_pay_details(employee):
	data = {}	
		
	for d in  frappe.db.sql("""
			SELECT
				rate_per_day, rate_per_hour, rate_per_hour_normal, parent
			FROM `tabMusterroll`
			WHERE parent = '{employee}'			
			ORDER BY from_date DESC
			LIMIT 1
		""".format(employee=employee), as_dict = True):

		data.setdefault(d.parent, frappe._dict(d))

	return data

def get_pay_details_dfg_gfg_opa_opt(employee,employee_type):	
		
	return  frappe.db.sql("""
			SELECT
				rate_per_day, rate_per_hour,salary
			FROM `tab{employee_type}`
			WHERE name = '{employee}'
			LIMIT 1
		""".format(employee_type=employee_type, employee=employee), as_dict = True)

def get_pay_opa(employee,employee_type):		
	return  frappe.db.sql("""
			SELECT
				rate_per_day, rate_per_hour,salary,is_lifer
			FROM `tab{employee_type}`
			WHERE name = '{employee}'
			LIMIT 1
		""".format(employee_type=employee_type, employee=employee), as_dict = True)

		

	
	