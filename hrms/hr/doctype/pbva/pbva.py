# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, date_diff, cint, add_months
from hrms.payroll.doctype.salary_structure.salary_structure import get_salary_tax
from erpnext.accounts.doctype.hr_accounts_settings.hr_accounts_settings import get_bank_account
from datetime import datetime

class PBVA(Document):
	def validate(self):
		#self.validate_duplicate()
		self.calculate_values()
		self.remove_zero_rows()

	def on_submit(self):
		cc_amount = {}
		for a in self.items:
			tax = get_salary_tax(a.amount)
			cost_center, ba = frappe.db.get_value("Employee", a.employee, ["cost_center", "business_activity"])
			cc = str(str(cost_center) + ":" + str(ba))
			if cc in cc_amount:
				cc_amount[cc]['amount'] = cc_amount[cc]['amount'] + a.amount
				cc_amount[cc]['tax'] = cc_amount[cc]['tax'] + a.tax_amount
				cc_amount[cc]['balance_amount'] = cc_amount[cc]['balance_amount'] + a.balance_amount
			else:
				row = {"amount": a.amount, "tax": a.tax_amount, "balance_amount":a.balance_amount}
				cc_amount[cc] = row

		self.post_journal_entry(cc_amount)

	def remove_zero_rows(self):
		if self.items:
			to_remove = []
			for d in self.items:
				if d.amount == 0:
					to_remove.append(d)
			[self.remove(d) for d in to_remove]
		i=1
		if self.items:
			for d in self.items:
				d.idx=i
				i+=1

	def validate_duplicate(self):
		doc = frappe.db.sql("select name from tabPBVA where docstatus != 2 and fiscal_year = \'"+str(self.fiscal_year)+"\' and name != \'"+str(self.name)+"\'")		
		if doc:
			frappe.throw("Can not create multiple PBVA for the same year")

	def calculate_values(self):
		if self.items:
			tot = tax = net = 0
			for a in self.items:
				a.tax_amount = get_salary_tax(a.amount)
				a.balance_amount = flt(a.amount) - flt(a.tax_amount)
				tot += flt(a.amount)
				tax += flt(a.tax_amount)
				net += flt(a.balance_amount)

			self.total_amount = tot
			self.tax_amount   = tax
			self.net_amount   = net
		else:
			frappe.throw("Cannot save without employee details")

	def post_journal_entry(self, cc_amount):
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = "PBVA for " + self.branch + "(" + self.name + ")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'PBVA payment against : ' + self.name
		je.posting_date = self.posting_date
		je.branch = self.branch

		pbva_account = frappe.db.get_single_value("HR Accounts Settings", "pbva_account")
		tax_account = frappe.db.get_single_value("HR Accounts Settings", "salary_tax_account")
		#expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		expense_bank_account = get_bank_account(self.branch)

		if not pbva_account:
			frappe.throw("Setup PBVA Account in HR Accounts Settings")
		if not tax_account:
			frappe.throw("Setup Salary Tax Account in HR Accounts Settings")
		if not expense_bank_account:
			frappe.throw("Setup Expense Bank Account for your branch")
		
		for key in cc_amount.keys():
			values = key.split(":")
			je.append("accounts", {
					"account": pbva_account,
					"reference_type": self.doctype,
					"reference_name": self.name,
					"cost_center": values[0],
					"debit_in_account_currency": flt(cc_amount[key]['amount']),
					"debit": flt(cc_amount[key]['amount']),
				})
		
			je.append("accounts", {
					"account": expense_bank_account,
					"cost_center": values[0],
					"credit_in_account_currency": flt(cc_amount[key]['balance_amount']),
					"credit": flt(cc_amount[key]['balance_amount']),
					"reference_type": self.doctype,
					"reference_name": self.name,
				})
			if flt(cc_amount[key]['tax'])>0:
			
				je.append("accounts", {
						"account": tax_account,
						"cost_center": values[0],
						"credit_in_account_currency": flt(cc_amount[key]['tax']),
						"credit": flt(cc_amount[key]['tax']),
						"reference_type": self.doctype,
						"reference_name": self.name,
						"party_check": 0
					})
		je.insert()

		self.db_set("journal_entry", je.name)

	def on_cancel(self):
		jv = frappe.db.get_value("Journal Entry", self.journal_entry, "docstatus")
		if jv != 2:
			frappe.throw("Can not cancel PBVA without canceling the corresponding journal entry " + str(self.journal_entry))
		else:
			self.db_set("journal_entry", "")


	@frappe.whitelist()
	def get_pbva_details(self):
		if not self.fiscal_year:
			frappe.throw("Fiscal Year is Mandatory")
		# if self.pbva_percent <= 0:
		# 	frappe.throw("PBVA percent cannot be 0 or less than 0")
		#start, end = frappe.db.get_value("Fiscal Year", self.fiscal_year, ["year_start_date", "year_end_date"])
		start = str(self.fiscal_year)+'-01-01'
		end   = str(self.fiscal_year)+'-12-31'
		
		query = """
				select
					e.name as employee,
					e.employee_name,
					e.employment_type,
					e.branch,
					e.date_of_joining,
					e.relieving_date,
					e.reason_for_leaving as leaving_type,
					e.salary_mode,
					e.bank_name,
					e.bank_ac_no,
					e.cost_center,
					e.grade,
					datediff(least(ifnull(e.relieving_date,'9999-12-31'),'{2}'),
					greatest(e.date_of_joining,'{1}'))+1 days_worked,
					(
						select	
							sd.amount
						from
						`tabSalary Detail` sd,
						`tabSalary Slip` sl
						where sd.parent = sl.name
						and sl.employee = e.name
						and sd.salary_component = 'Basic Pay'
						and sl.docstatus = 1
						and sl.fiscal_year = {0}
						and (sd.salary_component = 'Basic Pay'
						or exists(select 1 from `tabSalary Component` sc
						where sc.name = sd.salary_component
						and sc.is_pf_deductible = 1
						and sc.type = 'Earning'))
						and exists(select 1
						from `tabSalary Slip Item` ssi, 
						`tabSalary Structure` ss
						where ssi.parent = sl.name
						and ss.name = ssi.salary_structure
						and ss.eligible_for_pbva = 1)
						order by sl.month desc limit 1) as basic_pay,
					(
						select
							sum(sd.amount)
						from
						`tabSalary Detail` sd,
						`tabSalary Slip` sl
						where sd.parent = sl.name
						and sl.employee = e.name
						and sd.salary_component = 'Basic Pay'
						and sl.docstatus = 1
						and sl.fiscal_year = {0}
						and (sd.salary_component = 'Basic Pay'
						or sd.salary_component = 'Basic Pay Arrear'
						or exists(select 1 from `tabSalary Component` sc
						where sc.name = sd.salary_component
						and sc.is_pf_deductible = 1
						and sc.type = 'Earning'))
						and exists(select 1
						from `tabSalary Slip Item` ssi, `tabSalary Structure` ss
						where ssi.parent = sl.name
						and ss.name = ssi.salary_structure
						and ss.eligible_for_pbva = 1)) as total_basic_pay
						from tabEmployee e
						where (
								('{3}' = 'Active' and e.date_of_joining <= '{2}' and ifnull(e.relieving_date,'9999-12-31') > '{2}')
								or
								('{3}' = 'Left' and ifnull(e.relieving_date,'9999-12-31') between '{1}' and '{2}')
								or
								('{3}' = 'All' and e.date_of_joining <= '{2}' and ifnull(e.relieving_date,'9999-12-31') >= '{1}')
							)
							and not exists(
										select 1
											from `tabPBVA Details` bd, `tabPBVA` b
											where b.fiscal_year = '{0}'
											and b.name <> '{4}'
											and bd.parent = b.name
											and bd.employee = e.employee
											and b.docstatus in (0,1))
											order by e.branch
						""".format(self.fiscal_year, start, end, self.employee_status, self.name)
		
		entries = frappe.db.sql(query, as_dict=True)
		self.set('items', [])

		start = getdate(start)
		end = getdate(end)

		for d in entries:
			# d.amount = 0
			row = self.append('items', {})

			unit=frappe.db.get_value("Employee", d.employee, "unit")
			section=frappe.db.get_value("Employee", d.employee, "section")
			division=frappe.db.get_value("Employee", d.employee, "division")
			unit_rating=0
			if unit:
				unit_rating = frappe.db.get_value("Department",unit,"department_rating")
			elif section:
				unit_rating = frappe.db.get_value("Department",section,"department_rating")
			elif division:
				unit_rating = frappe.db.get_value("Department",division,"department_rating")
			else:
				frappe.throw("Employee doesn't have Unit, Section and Division")
			
			d.unit_rating=unit_rating

			
			# if frappe.db.get_single_value("HR Settings", "take_department_rating") == 1:
			# 	d.unit_rating = frappe.db.get_value(
			# 			"Performance Evaluation",
			# 			{
			# 				"employee": frappe.db.get_value("Department", d.department, "approver"),
			# 				"pms_calendar": self.fiscal_year
			# 			},
			# 			"final_score"
			# 	)
			# else:
			# 	d.unit_rating = self.company_achievement

			employee_rating =frappe.db.sql("""
                                    select count(name) as nos, sum(final_score) as final_score
                                    from `tabPerformance Evaluation` where docstatus = 1 and employee = '{}'
                                    and pms_calendar = '{}'
                                    """.format(d.employee, self.fiscal_year), as_dict = 1)
			
			 
			emp_group=frappe.db.get_value("Employee", d.employee, "employee_group") 

			# if frappe.db.get_value("Employee Group", emp_group, "employee_pf")== 0:
			# if not d.unit_rating or d.unit_rating == 0 and frappe.db.get_single_value("HR Settings", "take_department_rating") == 1:
			# 	d.unit_rating = flt(frappe.db.get_value("Department", d.department, "unit_rating"))

			d.unit_rating = 0 if not d.unit_rating else d.unit_rating * 0.5
			d.employee_rating = 0

			if employee_rating:
				d.employee_rating = employee_rating[0].final_score

			if not d.employee_rating:
				d.employee_rating = 0

			d.employee_rating = d.employee_rating * 0.5

			d.total_rating = d.unit_rating+d.employee_rating

			is_ceo=frappe.db.get_value("Employee", d.employee, "designation")=="Chief Executive Officer"

			
			if is_ceo:
				d.unit_rating=flt(self.company_achievement)*flt(0.5)
				d.employee_rating=flt(self.ceos_leadership_rating)*flt(0.5)
				d.total_rating=(flt(self.company_achievement)*flt(0.8))+(flt(self.ceos_leadership_rating)*flt(0.2))
				emp_ceip=frappe.db.get_single_value("HR Settings", "ceo_pbva_percent")
				
			else:
				emp_ceip=frappe.db.get_single_value("HR Settings", "rest_pbva_percent")


			d.pbva_percent = flt((d.total_rating/95)*flt(flt(emp_ceip)/100))*100
			# d.pbva_percent = flt((d.total_rating/95)*(self.pbva_percent),3)
			# else:
			# 	d.pbva_percent = flt(frappe.db.get_value("Employee Group", emp_group, "employee_pf"),3)

			d.total_basic_pay = 0 if not d.total_basic_pay else d.total_basic_pay
			if str(d.date_of_joining).split("-")[0] == str(self.fiscal_year) and flt(str(d.date_of_joining).split("-")[1]) < 10:
				d.days_worked = date_diff(datetime.strptime(str(self.fiscal_year)+"-12-31", "%Y-%m-%d").date(), datetime.strptime(str(self.fiscal_year)+"-"+str(int(str(d.date_of_joining).split("-")[1])+3)+"-"+str(d.date_of_joining).split("-")[2], "%Y-%m-%d").date())+1
			elif str(d.date_of_joining).split("-")[0] == str(self.fiscal_year) and flt(str(d.date_of_joining).split("-")[1]) >= 10:
				d.days_worked = 0
			if str(d.date_of_joining).split("-")[0] == str(int(self.fiscal_year)-1) and flt(str(d.date_of_joining).split("-")[1]) > 9:
				d.days_worked = date_diff(datetime.strptime(str(self.fiscal_year)+"-12-31", "%Y-%m-%d").date(), datetime.strptime(str(add_months(d.date_of_joining,6)), "%Y-%m-%d").date())+1
			if d.status == 'Active':
				days_in_year=365

				d.amount = flt((flt(flt(d.pbva_percent/100)*d.total_basic_pay)/days_in_year)*d.days_worked,2)
			else:
				d.amount = flt(flt(flt(d.pbva_percent/100)*d.total_basic_pay),2)
			row.update(d)
			
# @frappe.whitelist()
# def get_pbva_percent(employee):
# 	group = frappe.db.get_value("Employee", employee, "employee_group")
# 	if group in ("Chief Executive Officer", "Executive"):
# 		return "above"
# 	else:
# 		return "below"


					# ((
					# 	select
					# 		sum(sd.amount)
					# 	from `tabSalary Detail` sd, `tabSalary Slip` sl
					# 	where sd.parent = sl.name
					# 	and sl.employee = e.name
					# 	and sd.salary_component = 'Basic Pay'
					# 	and sl.docstatus = 1
					# 	and sl.fiscal_year = {0}
					# 	and (sd.salary_component = 'Basic Pay'
					# 	or exists(select 1 from `tabSalary Component` sc
					# 	where sc.name = sd.salary_component
					# 	and sc.is_pf_deductible = 1
					# 	and sc.type = 'Earning'))
					# 	and exists
					# 	(
					# 		select 1
					# 		from `tabSalary Slip Item` ssi, `tabSalary Structure` ss
					# 		where ssi.parent = sl.name
					# 		and ss.name = ssi.salary_structure
					# 		and ss.eligible_for_pbva = 1
					# 	)
					# )/100*{5}) as amount