# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate
from erpnext.accounts.utils import get_child_cost_centers
from datetime import datetime
import calendar

class OtherContribution(Document):
	def validate(self):
		self.update_defaults()
		self.validate_amounts()
		self.validate_group_cost_center()
				
	def on_submit(self):
		self.update_salary_structure()
		self.post_journal_entry()

	def on_cancel(self):
		if self.reference and frappe.db.exists("Journal Entry", {"name":self.reference, "docstatus": ("<",2)}):
			frappe.throw(_('You need to cancel Journal Entry <a href="#Form/Journal Entry/{0}" target="_blank">{0}</a> first.').format(self.reference),title="Not Permitted")
		
		self.update_salary_structure(True)

	def validate_group_cost_center(self):
		if frappe.session.user != "Administrator":
			user_cc = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "cost_center")

			if not user_cc or user_cc not in self.get_cc_list(self.group_cost_center):
				frappe.throw(_("You do not have permission to access cost center <b>{0}</b>").format(self.group_cost_center), title="No permission")
	
	def validate_amounts(self):
		total_noof_employees      = 0
		total_noof_contributors   = 0
		total_contribution_amount = 0

		for i in self.get("items"):
			if flt(i.contribution) < 0:
				frappe.throw(_("Row#{0} : Contribution amount cannot be a negative value").format(i.idx), title="Invalid data")
			elif self.employee == i.employee and flt(i.contribution) > 0:
				frappe.msgprint(_("Row#{0} : Employee to whom the contribution is meant is also in the contributors list").format(i.idx))
			else:
				pass
			
			total_noof_employees += 1
			if flt(i.contribution) > 0:
				total_noof_contributors += 1
				total_contribution_amount += flt(i.contribution)
				
		self.total_noof_employees      = total_noof_employees
		self.total_noof_contributors   = total_noof_contributors
		self.total_contribution_amount = total_contribution_amount

		if flt(self.total_contribution_amount) == 0:
			frappe.throw(_("Total contribution amount cannot be zero"), title="Invalid data")
					
	def update_defaults(self):
		self.posting_date = nowdate()

		if not self.salary_component:
			frappe.throw(_("Missing default value for field salary_component under DocType master. Please contact Administrator."), title="Data missing")
				
		if not frappe.db.exists("Salary Component", self.salary_component):
			frappe.throw(_("Salary component <b>`{0}`</b> not found").format(self.salary_component), title="Data missing")

		if self.docstatus < 2:
			self.reference = None
		
	def post_journal_entry(self):
		expense_bank_account      = frappe.db.get_value("Branch", self.contributing_branch, "expense_bank_account")
		salary_component = frappe.get_doc("Salary Component", self.salary_component)
		# advance_other_account = (
		# 	salary_component.accounts[0].account
		# 	if salary_component.accounts
		# 	else None
		# )
		advance_other_account = frappe.db.get_value(
			"Salary Component Account",
			{"parent": self.salary_component},
			"account",
			order_by="idx",
		)
		# advance_other_account     = frappe.db.get_value("Salary Component", self.salary_component, "gl_head")
		default_business_activity = frappe.db.get_value("Business Activity", {"is_default": 1}, "name")
		default_cost_center       = frappe.db.get_value("Company", self.company, "cost_center")

		if not expense_bank_account:
			frappe.throw(_("Please define <b>Expense Bank Account</b> for the branch <b>{0}</b>").format(self.contributing_branch), title="Data missing")
		elif not advance_other_account:
			frappe.throw(_("Please define Account for the salary component <b>{0}</b>").format(self.salary_component), title="Data missing")
		elif not default_business_activity:
			frappe.throw(_("Please define default business activity under <b>Business Activity</b>"), title="Data missing")
		elif not default_cost_center:
			frappe.throw(_("Please define default cost center under <b>Company</b> master"), title="Data missing")
		else:
			pass
		
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = self.title + " ("+self.name+")"
		je.voucher_type = 'Bank Entry'
		je.naming_series = 'Bank Payment Voucher'
		je.remark = 'Payment against : ' + je.title
		je.posting_date = self.posting_date
		je.branch = self.contributing_branch
		je.pay_to_recd_from = self.employee_name

		for i in self.get("items"):
			je.append("accounts", {
				"account": advance_other_account,
				"business_activity": i.business_activity,
				"reference_type": "Other Contribution",
				"reference_name": self.name,
				"cost_center": i.cost_center,
				"debit_in_account_currency": flt(i.contribution),
				"debit": flt(i.contribution),
				"party_type": "Employee",
				"party": i.employee
			})
				
		je.append("accounts", {
			"account": expense_bank_account,
			"business_activity": default_business_activity,
			"reference_type": "Other Contribution",
			"reference_name": self.name,
			"cost_center": default_cost_center,
			"credit_in_account_currency": flt(self.total_contribution_amount),
			"credit": flt(self.total_contribution_amount),
		})
		je.insert()
		self.db_set("reference", je.name)
		frappe.msgprint(_('Journal Entry <a href="#Form/Journal Entry/{0}" target="_blank">{0}</a> posted to accounts for payment').format(je.name))
			
	def update_salary_structure(self, cancel=False):
		from_date = self.application_date
		year = str(self.application_date).split("-")[0]
		month = str(self.application_date).split("-")[1]
		date = calendar.monthrange(int(year),int(month))
		to_date = str(year)+"-"+str(month)+"-"+str(date[1])

		for i in self.get("items"):
			if flt(i.contribution) > 0:
				if cancel:
					rem_list = []
					if i.salary_structure:
						doc = frappe.get_doc("Salary Structure", i.salary_structure)
						for d in doc.get("deductions"):
							if d.salary_component == self.salary_component and self.name in (d.reference_number, d.ref_docname):
								rem_list.append(d)
							if d.salary_component == "Other Contribution" and d.from_date < self.application_date and str(d.from_date).split("-")[0]+"-"+str(d.from_date).split("-")[1] != str(self.application_date).split("-")[0]+"-"+str(self.application_date).split("-")[1]:
								rem_list.append(d)

						[doc.remove(d) for d in rem_list]
						doc.save(ignore_permissions=True)
				else:
					rem_list = []
					if i.salary_structure:
						doc = frappe.get_doc("Salary Structure", i.salary_structure)
						for d in doc.get("deductions"):
							if d.salary_component == "Other Contribution" and datetime.strptime(str(d.from_date),"%Y-%m-%d") < datetime.strptime(str(self.application_date),"%Y-%m-%d") and str(d.from_date).split("-")[0]+"-"+str(d.from_date).split("-")[1] != str(self.application_date).split("-")[0]+"-"+str(self.application_date).split("-")[1]:
								rem_list.append(d)

						[doc.remove(d) for d in rem_list]
						doc.save(ignore_permissions=True)
					if frappe.db.exists("Salary Structure", {"employee": i.employee, "is_active": "Yes"}):
						doc = frappe.get_doc("Salary Structure", {"employee": i.employee, "is_active": "Yes"})
						row = doc.append("deductions",{})
						row.salary_component        = self.salary_component
						row.amount                  = flt(i.contribution)
						row.default_amount          = flt(i.contribution)
						row.reference_number        = self.name
						row.ref_docname             = self.name
						row.total_deductible_amount = flt(i.contribution)
						row.total_deducted_amount   = 0
						row.total_outstanding_amount= flt(i.contribution)
						row.total_days_in_month     = 0
						row.working_days            = 0
						row.leave_without_pay       = 0
						row.payment_days            = 0
						row.from_date = from_date
						row.to_date = to_date 
						# if not row.bank_branch:
						# 	frappe.throw(f"Bank Branch missing in row {row.idx}")
						doc.save(ignore_permissions=True)
						i.db_set("salary_structure", doc.name, update_modified=False)
					else:
						frappe.throw(_("No active salary structure found for employee {0} {1}").format(i.employee, i.employee_name), title="No Data Found")

	def remove_paid_contribution(self):
		current_date = datetime.strptime(str(nowdate()), "%Y-%m-%d")
		component_list = frappe.db.sql("""
			select name from `tabSalary Detail` where salary_component = 'Other Contribution' and to_date < '{0}'
			or (from_date is NULL and to_date is NULL)
		""".format(current_date))
		if component_list:
			for a in component_list:
				frappe.db.sql("""
					delete from `tabSalary Detail` where name = '{0}'
				""".format(a.name))

	@frappe.whitelist()
	def remove_employee(self):
		if self.employee:
			for i in self.get('items'):
				if i.employee == self.employee:
					self.remove(i)
			
	def get_cc_list(self, group_cc):
		cc_list = []
		qry = "select name, is_group from `tabCost Center` where parent_cost_center = '{0}'".format(group_cc)
		for c in frappe.db.sql(qry, as_dict=True):
			if c.is_group:
				cc_list += self.get_cc_list(c.name)
			else:
				cc_list += [str(c.name)]

		return cc_list

	@frappe.whitelist()
	def update_amounts(self):
		grades = {}
		if self.contribution_type == "Grade":
			for i in frappe.db.sql("select name, other_contribution from `tabEmployee Grade`", as_dict=True):
				if not grades.has_key(str(i.name)):
					grades[str(i.name)] = i.other_contribution

		for i in self.get('items'):
			i.contribution = flt(self.contribution) if self.contribution_type == "Flat Rate" else flt(grades.get(i.employee_grade))

	@frappe.whitelist()
	def get_employees(self):
		self.set('items', [])
		cc_list = [str(self.group_cost_center)]
		cc_list += self.get_cc_list(self.group_cost_center)
		format_string = ','.join(["'%s'"]*len(cc_list))
		format_string = format_string % tuple(cc_list)

		qry = """
			select
				name, employee_name, employment_type,
				employee_group, grade, 
				designation, branch, cost_center,
				business_activity
			from `tabEmployee` e
			where cost_center in ({0})
			and status = 'Active'
			and exists(select 1
						from `tabSalary Structure` sst
						where sst.employee = e.name
						and sst.is_active = 'Yes')
			order by cost_center, name
		""".format(format_string)

		for e in frappe.db.sql(qry, as_dict=True):
			if not self.employee == e.name:
				e.employee = e.name
				e.employee_grade = e.grade
				row = self.append('items', {})
				row.update(e)

		self.update_amounts()

@frappe.whitelist()
def get_branches(doctype=None, txt=None, searchfield=None, start=None, page_len=None, filters=None):
	if filters.get("parent_cost_center"):
		allccs = get_child_cost_centers(filters.get("parent_cost_center"))
		return frappe.db.sql("""
		select name from `tabBranch`
		where cost_center in {} and disabled != 1 
		""".format(tuple(allccs)))   
	else:
		frappe.throw("Please select Contributing Group first.")