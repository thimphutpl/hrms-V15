# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from datetime import date
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, today
from frappe.utils import date_diff, flt, cint, money_in_words
from hrms.hr.doctype.leave_application.leave_application import get_leaves_for_period
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.hr.utils import set_employee_name, validate_active_employee
from hrms.payroll.doctype.salary_structure.salary_structure import get_basic_and_gross_pay, get_salary_tax
from hrms.hr.hr_custom_functions import get_salary_tax
from erpnext.custom_workflow import notify_workflow_states
from erpnext.accounts.doctype.hr_accounts_settings.hr_accounts_settings import get_bank_account
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

class LeaveEncashment(Document):
	def validate(self):			
		set_employee_name(self)
		validate_active_employee(self.employee)		
		self.get_leave_balance()
		self.validate_balances()
		self.check_duplicate_entry()
		if not self.encashment_date:
		 	self.encashment_date = getdate(nowdate())
		if self.workflow_state != "Approved":
			notify_workflow_states(self)

	def before_submit(self):
		if self.encashment_amount <= 0:			
			frappe.throw(_("You can only submit Leave Encashment for a valid encashment amount"))

	def on_submit(self):
		# self.post_expense_claim()
		self.post_accounts_entry()
		self.create_leave_ledger_entry()
		notify_workflow_states(self)	
	
	def post_accounts_entry(self):
		if not self.cost_center:
			frappe.throw("Setup Cost Center for employee in Employee Information")

		expense_account = frappe.db.get_single_value("HR Accounts Settings", "leave_encashment_account")
		if not expense_account:
			frappe.throw("Setup Leave Encashment Account in Company")

		tax_account = frappe.db.get_single_value("HR Accounts Settings", "salary_tax_account")
		expense_bank_account = get_bank_account(self.branch)
		if not expense_bank_account:
			frappe.throw("Setup Default Expense Bank Account for your Branch")
		if not tax_account:
			frappe.throw("Setup Tax Account in Company")
		# Journal Entry		
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = 'Leave Encashment Payable - ' + str(self.employee_name) + "(" + str(self.employee) + ")"
		je.voucher_type = "Journal Entry"
		je.naming_series = "Journal Voucher"
		je.company = self.company
		je.branch = self.branch
		je.remark = 'Payable against Leave Encashment: ' + self.name
		je.user_remark = 'Leave Encashment Payable - ' + str(self.employee_name) + "(" + str(self.employee) + ")"
		je.posting_date = today()
		je.total_amount_in_words =  money_in_words(flt(self.payable_amount))

		je.append("accounts", {
				"account": expense_account,
				"debit_in_account_currency": flt(self.encashment_amount,2),
				"debit": flt(self.encashment_amount,2),
				"reference_type": "Leave Encashment",
				"reference_name": self.name,
				"cost_center": self.cost_center,
		})

		if flt(self.encashment_tax):
			je.append("accounts", {
					"account": tax_account,
					"credit_in_account_currency": flt(self.encashment_tax,2),
					"credit": flt(self.encashment_tax,2),
					"reference_type": "Leave Encashment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
			})
		payable_account= frappe.db.get_single_value("HR Accounts Settings", "salary_payable_account")
		# payable_account = frappe.db.get_value("Company",self.company, "default_expense_claim_payable_account") #Added by Thukten
		if flt(self.payable_amount) > 0:
			je.append("accounts", {
					"account": payable_account,
					"reference_type": "Leave Encashment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"credit_in_account_currency": flt(self.payable_amount,2),
					"credit": flt(self.payable_amount,2),
					"party_type": "Employee",
					"party": self.employee,
				})
		je.insert()
		je.submit()
		je_references = str(je.name)
		#Bank Entry		
		jebp = frappe.new_doc("Journal Entry")
		jebp.flags.ignore_permissions = 1 
		jebp.title = 'Leave Encashment Payment - ' + str(self.employee_name) + "(" + str(self.employee) + ")"
		jebp.voucher_type = "Bank Entry"
		jebp.naming_series = "Bank Payment Voucher"
		jebp.company = self.company
		jebp.branch = self.branch
		jebp.remark = 'Payment against Leave Encashment: ' + self.name
		jebp.user_remark = 'Leave Encashment Payment - ' + str(self.employee_name) + "(" + str(self.employee) + ")"
		jebp.posting_date = today()
		jebp.total_amount_in_words =  money_in_words(flt(self.payable_amount,2))
		jebp.append("accounts", {
				"account": payable_account,
				"debit_in_account_currency": flt(self.payable_amount,2),
				"debit": flt(self.payable_amount,2),
				"reference_type": "Journal Entry",
				"reference_name": je.name,
				"cost_center": self.cost_center,
				"party_type": "Employee",
				"party": self.employee,
		})
		payable_account= frappe.db.get_single_value("HR Accounts Settings", "salary_payable_account")
		# payable_account = frappe.db.get_value("Company",self.company, "default_expense_claim_payable_account") #Added by Thukten
		if flt(self.payable_amount) > 0:
			jebp.append("accounts", {
					"account": expense_bank_account,
					"reference_type": "Leave Encashment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"credit_in_account_currency": flt(self.payable_amount,2),
					"credit": flt(self.payable_amount,2),
					"party_type": "Employee",
					"party": self.employee,
				})
		jebp.insert()
		je_references += ", "+jebp.name
		self.db_set("journal_entry", je_references)

		# self.create_leave_ledger_entry()
	def on_cancel(self):
		if self.leave_allocation:
			frappe.db.set_value(
				"Leave Allocation",
				self.leave_allocation,
				"total_leaves_encashed",
				frappe.db.get_value("Leave Allocation", self.leave_allocation, "total_leaves_encashed")
				- self.encashable_days,
			)
		self.create_leave_ledger_entry(submit=False)
		self.check_journal_entry()

	def check_journal_entry(self):
		if self.journal_entry:			
			for je in str(self.journal_entry).split(", "):
				if frappe.db.get_value("Journal Entry", je, "docstatus") < 2:
					frappe.throw("Please cancel/delete Journal Entry {} first".format(frappe.get_desk_link("Journal Entry", je)))

	def post_expense_claim(self):
		cost_center = frappe.get_value("Employee", self.employee, "cost_center")
		branch = frappe.get_value("Employee", self.employee, "branch")
		company =frappe.get_value("Employee", self.employee, "company")
		default_payable_account = frappe.get_cached_value("Company", company, "default_expense_claim_payable_account")
		taxt_account_head = frappe.get_cached_value("Company", company, "salary_tax_account")

		expense_claim 					= frappe.new_doc("Expense Claim")
		expense_claim.flags.ignore_mandatory = True
		expense_claim.company 			= company
		expense_claim.employee 			= self.employee
		expense_claim.payable_account 	= default_payable_account
		expense_claim.cost_center 		= cost_center 
		expense_claim.is_paid 			= cint(0)
		expense_claim.expense_approver	= frappe.db.get_value('Employee',self.employee,'expense_approver')
		expense_claim.branch			= branch

		expense_claim.append('expenses',{
			"expense_date":			nowdate(),
			"expense_type":			self.doctype,
			"amount":				self.basic_pay,
			"sanctioned_amount":	self.basic_pay,
			"reference_type":		self.doctype,
			"reference":			self.name,
			"cost_center":			cost_center
		})
		expense_claim.append('taxes',{
			"account_head":	taxt_account_head,
			"add_or_deduct" :"Deduct",
			"tax_amount":	self.encashment_tax,
			"cost_center":	cost_center,
			"description":	"Leave Encashment Tax"
		})
		expense_claim.docstatus = 0

		expense_claim.save(ignore_permissions=True)
		expense_claim.submit()
		self.db_set("expense_claim", expense_claim.name)
		frappe.db.commit()
		frappe.msgprint(
			_("Expense Claim record {0} created")
			.format("<a href='/app/Form/Expense Claim/{0}'>{0}</a>")
			.format(expense_claim.name))

	def create_leave_ledger_entry(self, submit=True):
		args = frappe._dict(
			leaves=self.encashment_days * -1,
			from_date=self.encashment_date,
			to_date=self.encashment_date,
			is_carry_forward=0
		)
		create_leave_ledger_entry(self, args, submit)

		# create reverse entry for expired leaves
		to_date = self.get_leave_allocation().get('to_date')
		if to_date < getdate(nowdate()):
			args = frappe._dict(
				leaves=self.encashment_days,
				from_date=to_date,
				to_date=to_date,
				is_carry_forward=0
			)
			create_leave_ledger_entry(self, args, submit)

	def update_employee_details(self):
		self.encashment_days      = 0
		self.balance_before     = 0
		self.balance_after      = 0

		if self.employee:                
				doc = frappe.get_doc("Employee", self.employee)
				self.employee_name      = doc.employee_name
				self.employment_type    = doc.employment_type
				self.employee_group     = doc.employee_group
				self.grade  = doc.grade
				self.branch             = doc.branch
				self.cost_center        = doc.cost_center
				self.department         = doc.department
				self.division           = doc.division
				self.section            = doc.section

	def get_current_year_dates(self):
		from_date = date(date.today().year,1,1).strftime('%Y-%m-%d')
		to_date = date(date.today().year,12,31).strftime('%Y-%m-%d')
		return from_date, to_date                            

	def validate_balances(self):		
		msg = ''
		#le = get_le_settings()                                                                         # Line commented by SHIV on 2018/10/15
		le = frappe.get_doc("Employee Group",frappe.db.get_value("Employee",self.employee,"employee_group")) # Line added by SHIV on 2018/10/15
		if flt(self.balance_before) <= flt(le.min_encashment_days):
			msg = "Minimum leave balance {0} required to encash.".format(le.encashment_min)
			# frappe.throw(msg)
			if self.employment_type =="Deputation" and flt(self.balance_before) < flt(encashment_min):
			        msg = "Minimum leave balance {0} required to encash.".format(le.encashment_min)
			elif self.employment_type !="Deputation":
			        msg = "Minimum leave balance {0} required to encash.".format(le.encashment_min)

		if flt(self.balance_after) < 0:
				msg = "Insufficient leave balance"
				InsufficientError="Insufficient leave balance"

		if msg:
				frappe.throw(_("{0}").format(msg), InsufficientError)
	def get_leave_balance(self):		
		self.update_employee_details()
		if self.employee:
				group_doc = frappe.get_doc("Employee Group", self.employee_group)
				self.encashment_days  = group_doc.min_encashment_days				
				self.balance_before = get_leave_balance_on(self.employee, self.leave_type, str(self.encashment_date))				
				self.balance_after  = flt(self.balance_before) - flt(self.encashment_days)			
	
	def check_duplicate_entry(self):
		# Check if there's already a draft entry
		draft_count = frappe.db.count(self.doctype, {
			"employee": self.employee,
			"leave_period": self.leave_period,
			"leave_type": self.leave_type,
			"docstatus": 0  # Check only for draft documents
		})

		if draft_count > 0:
			frappe.throw("You already have a draft encashment request for leave period {}. Please submit or cancel it before creating a new one.".format(
				frappe.bold(self.leave_period)
			))

		# Count submitted entries
		submitted_count = frappe.db.count(self.doctype, {
			"employee": self.employee,
			"leave_period": self.leave_period,
			"leave_type": self.leave_type,
			"docstatus": 1  # Check only for submitted documents
		}) or 0  # Default to 0 if no records found

		# Get employee group and frequency
		employee_grp = frappe.db.get_value("Employee", self.employee, "employee_group")
		frequency = frappe.db.get_value("Employee Group", employee_grp, "encashment_frequency")

		if flt(submitted_count) >= flt(frequency):
			frappe.throw("You had already encashed {} time(s) for leave period {}.".format(
				frappe.bold(submitted_count), frappe.bold(self.leave_period)
			))


	@frappe.whitelist()
	def get_leave_details_for_encashment(self):
		salary_structure =  frappe.db.sql("""select name 
						from `tabSalary Structure`
						where employee='{}'
						and'{}' >= from_date 
						order by from_date desc limit 1""".format(self.employee, self.encashment_date)
					)
		
		if not salary_structure:
			frappe.throw(
				_("No Salary Structure assigned for Employee {0} on given date {1}").format(
					self.employee, self.encashment_date
				)
			)

		if not frappe.db.get_value("Leave Type", self.leave_type, "allow_encashment"):
			frappe.throw(_("Leave Type {0} is not encashable").format(self.leave_type))
		allocation = self.get_leave_allocation()		
		leave_bal_mr_cl=self.get_laave_bal_mr()		
		
		if not allocation:
			frappe.throw(
				_("No Leaves Allocated to Employee: {0} for Leave Type: {1}").format(
					self.employee, self.leave_type
				)
			)
		
		self.leave_balance = (
			allocation.total_leaves_allocated
			- allocation.carry_forwarded_leaves_count
			# adding this because the function returns a -ve number
			+ get_leaves_for_period(
				self.employee, self.leave_type, allocation.from_date, self.encashment_date
			)
		)		
		employee_group = frappe.db.get_value("Employee", self.employee, "employee_group")
		encashment_min = frappe.db.get_value("Employee Group", employee_group, "encashment_min")
		encashable_days = frappe.db.get_value("Employee Group", employee_group, "max_encashment_days")
		
		if leave_bal_mr_cl is None:			
			self.balance_before=self.leave_balance
		else:			
			self.balance_before=self.leave_balance+leave_bal_mr_cl.leaves
		
		self.balance_after=self.balance_before-encashable_days
		if self.balance_before < flt(encashment_min):		
			frappe.throw(_("Minimum '{}' days is Mandatory for Encashment").format(cint(encashment_min)),title="Leave Balance")
		
		# self.encashable_days = encashable_days if encashable_days > 0 else 0
		self.encashable_days = encashable_days if encashable_days and encashable_days > 0 else 0

		self.encashment_days = frappe.db.get_value("Employee Group", employee_group, "max_encashment_days")
		# per_day_encashment = frappe.db.get_value("Salary Structure", salary_structure, "leave_encashment_amount_per_day")
		
		# getting encashment amount from salary structure
		pay = get_basic_and_gross_pay(employee=self.employee, effective_date=today())
		leave_encashment_type = frappe.db.get_value("Employee Group", employee_group, "leave_encashment_type")
		if leave_encashment_type == "Flat Amount":
			self.flat_amount	   	= flt(employee_group.leave_encashment_amount)
			self.encashment_amount 	= flt(employee_group.leave_encashment_amount)
		elif leave_encashment_type == "Basic Pay":
			self.basic_pay			= flt(pay.get("basic_pay"))
			self.encashment_amount 	= (flt(pay.get("basic_pay"))/30)*flt(self.encashment_days)
		elif leave_encashment_type == "Gross Pay":
			self.gross_pay			= flt(pay.get("gross_pay"))
			self.encashment_amount 	= (flt(pay.get("gross_pay"))/30)*flt(self.encashment_days)
		else:
			self.encashment_amount = 0
		

		self.leave_encashment_type = leave_encashment_type
		# self.salary_structure = salary_structure
		self.encashment_tax = get_salary_tax(self.encashment_amount)
		# frappe.throw(str(self.encashment_tax))
		self.payable_amount = flt(self.encashment_amount) - flt(self.encashment_tax)

		self.leave_allocation = allocation.name
		return True

	def get_leave_allocation(self):		
		date = self.encashment_date or getdate()

		LeaveAllocation = frappe.qb.DocType("Leave Allocation")
		leave_allocation = (
			frappe.qb.from_(LeaveAllocation)
			.select(
				LeaveAllocation.name,
				LeaveAllocation.from_date,
				LeaveAllocation.to_date,
				LeaveAllocation.total_leaves_allocated,
				LeaveAllocation.carry_forwarded_leaves_count,
			)
			.where(
				((LeaveAllocation.from_date <= date) & (date <= LeaveAllocation.to_date))
				& (LeaveAllocation.docstatus == 1)
				& (LeaveAllocation.leave_type == self.leave_type)
				& (LeaveAllocation.employee == self.employee)
			)
		).run(as_dict=True)

		return leave_allocation[0] if leave_allocation else None

	def get_laave_bal_mr(self):		
		date = self.encashment_date or getdate()

		Leavebal = frappe.qb.DocType("Leave Ledger Entry")
		
		leave_bal = (
			frappe.qb.from_(Leavebal)
			.select(
				Leavebal.name,
				Leavebal.from_date,
				Leavebal.to_date,
				
				Leavebal.leaves
			)
			.where(
				((Leavebal.from_date <= date) & (date <= Leavebal.to_date))
				& (Leavebal.docstatus == 1)
				& (Leavebal.leave_type == self.leave_type)
				& (Leavebal.employee == self.employee)
				& (Leavebal.transaction_type == 'Merge CL To EL')
			)
		).run(as_dict=True)	

		return leave_bal[0] if leave_bal else None

	def create_leave_ledger_entry(self, submit=True):
		args = frappe._dict(
			leaves=self.encashable_days * -1,
			from_date=self.encashment_date,
			to_date=self.encashment_date,
			is_carry_forward=0,
		)
		create_leave_ledger_entry(self, args, submit)

		# create reverse entry for expired leaves
		leave_allocation = self.get_leave_allocation()
		if not leave_allocation:
			return

		to_date = leave_allocation.get("to_date")
		if to_date < getdate(nowdate()):
			args = frappe._dict(
				leaves=self.encashable_days, from_date=to_date, to_date=to_date, is_carry_forward=0
			)
			create_leave_ledger_entry(self, args, submit)


def create_leave_encashment(leave_allocation):
	"""Creates leave encashment for the given allocations"""
	for allocation in leave_allocation:
		if not get_assigned_salary_structure(allocation.employee, allocation.to_date):
			continue
		leave_encashment = frappe.get_doc(
			dict(
				doctype="Leave Encashment",
				leave_period=allocation.leave_period,
				employee=allocation.employee,
				leave_type=allocation.leave_type,
				encashment_date=allocation.to_date,
			)
		)
		leave_encashment.insert(ignore_permissions=True)

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return
	if "HR Support" in user_roles:
		return """(
			`tabLeave Encashment`.owner = '{user}'
			or
			exists(select 1
			from `tabEmployee`
			where `tabEmployee`.branch = `tabLeave Encashment`.branch
			and `tabEmployee`.user_id = '{user}')
		)""".format(user=user)
	return """(
		`tabLeave Encashment`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee`
			where `tabEmployee`.name = `tabLeave Encashment`.employee
			and `tabEmployee`.user_id = '{user}')
		or
		(`tabLeave Encashment`.approver = '{user}' and `tabLeave Encashment`.workflow_state not in ('Draft','Rejected','Approved','Cancelled'))
	)""".format(user=user)