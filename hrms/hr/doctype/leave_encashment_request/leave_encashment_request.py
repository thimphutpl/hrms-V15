# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, flt, today, money_in_words
from hrms.hr.utils import set_employee_name
from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import get_assigned_salary_structure
from hrms.hr.doctype.leave_ledger_entry.leave_ledger_entry import create_leave_ledger_entry
from hrms.hr.doctype.leave_allocation.leave_allocation import get_unused_leaves
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on
from hrms.payroll.doctype.salary_structure.salary_structure import get_basic_and_gross_pay
from hrms.hr.hr_custom_functions import get_salary_tax
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from erpnext.accounts.doctype.hr_accounts_settings.hr_accounts_settings import get_bank_account

class LeaveEncashmentRequest(Document):
	def validate(self):
		self.cal_encash_carrday()
		# import pdb; pdb.set_trace()
		# self.check_duplicate_entry()
		# set_employee_name(self)
		# self.get_leave_details_for_encashment()
		# self.validate_encashment_days()
		# validate_workflow_states(self)
		# if self.workflow_state != "Approved":
		# 	notify_workflow_states(self)
	def cal_encash_carrday(self):
		self.encashment_days = self.total_leave_balance - self.carry_forward_days
		if self.encashment_days > 30:
			frappe.throw("Please adjust your carry forward days so that the total encashment leave balance minus the carry forward days does not exceed 30 days")
		if self.carry_forward_days > self.total_leave_balance:
			frappe.throw("Carry forward Days cannot be greater than total leave balance")
	# def before_submit(self):
	# 	if self.encashment_amount <= 0:
	# 		frappe.throw(_("You can only submit Leave Encashment for a valid encashment amount"))

	# def on_submit(self):
	# 	if not self.leave_allocation:
	# 		self.leave_allocation = self.get_leave_allocation().get('name')
	# 	# Following code commented by SHIV on 2020/10/01
	# 	# Additional Salary is disabled
	# 	'''
	# 	additional_salary = frappe.new_doc("Additional Salary")
	# 	additional_salary.company = frappe.get_value("Employee", self.employee, "company")
	# 	additional_salary.employee = self.employee
	# 	additional_salary.salary_component = frappe.get_value("Leave Type", self.leave_type, "earning_component")
	# 	additional_salary.payroll_date = self.encashment_date
	# 	additional_salary.amount = self.encashment_amount
	# 	additional_salary.submit()

	# 	self.db_set("additional_salary", additional_salary.name)
	# 	'''

	# 	# Set encashed leaves in Allocation
	# 	frappe.db.set_value("Leave Allocation", self.leave_allocation, "total_leaves_encashed",
	# 			frappe.db.get_value('Leave Allocation', self.leave_allocation, 'total_leaves_encashed') + self.encashment_days)

	# 	self.create_leave_ledger_entry()
	# 	self.post_accounts_entry()
	# 	notify_workflow_states(self)

	# Following method added by SHIV on 2020/10/02
	def before_cancel(self):
		self.check_gl_entry()

	def on_cancel_after_draft(self):
		validate_workflow_states(self)
		notify_workflow_states(self)

	def on_cancel(self):
		if self.additional_salary:
			frappe.get_doc("Additional Salary", self.additional_salary).cancel()
			self.db_set("additional_salary", "")

		if self.leave_allocation:
			frappe.db.set_value("Leave Allocation", self.leave_allocation, "total_leaves_encashed",
				frappe.db.get_value('Leave Allocation', self.leave_allocation, 'total_leaves_encashed') - self.encashable_days)
		self.create_leave_ledger_entry(submit=False)
		notify_workflow_states(self)
			
	def validate_encashment_days(self):
		employee_group = frappe.get_doc("Employee Group", self.employee_group)
		if self.encashment_days > self.leave_balance:
			frappe.throw("Cannot encash more than leave balance")
		# if flt(self.encashment_days) <= 0 or (not flt(employee_group.min_encashment_days) <= \
		# 		self.encashment_days <= flt(employee_group.max_encashment_days)):
		# 	frappe.throw(_("Encashment Days should be between {} and {}").format(employee_group.min_encashment_days, employee_group.max_encashment_days))		
		if flt(self.encashment_days) <= 0 or self.encashment_days < flt(employee_group.min_encashment_days):
			frappe.throw(_("Encashment Days should be equal to {}").format(employee_group.min_encashment_days))
		# if flt(self.encashment_days) > flt(self.encashable_days):
		# 	frappe.throw(_("Encashment Days should be equal to {}").format(self.encashable_days))		


	def check_duplicate_entry(self):
		for rec in frappe.db.get_all("Leave Encashment", {"employee": self.employee, "leave_period": self.leave_period, "leave_type": self.leave_type, \
			"name": ("!=", self.name), "docstatus": 0, "workflow_state": ("!=","Rejected")}, ["name", "workflow_state"]):
			frappe.throw(_("There is already another request via {} in status {}").format(frappe.get_desk_link(self.doctype, rec.name), frappe.bold(rec.workflow_state)), title="Not Permitted")

	# Following method added by SHIV on 2020/10/02
	def check_gl_entry(self):
		if self.journal_entry:
			if frappe.db.exists("Journal Entry", {"name": self.journal_entry, "docstatus": ("<", 2)}):
				frappe.throw("You cannot cancel this document without cancelling the journal entry")

	def get_leave_details_for_encashment(self):
		if not self.encashment_date:
			self.encashment_date = getdate(nowdate())

		# Ver.20201001 Begins, by SHIV on 2020/10/01
		# Leave Encashment logic is replaced by old version
		salary_structure = {}


		# Following code commented by SHIV on 2020/10/01
		'''
		salary_structure = get_assigned_salary_structure(self.employee, self.encashment_date or getdate(nowdate()))
		if not salary_structure:
			frappe.throw(_("No Salary Structure assigned for Employee {0} on given date {1}").format(self.employee, self.encashment_date))
		'''
		# Ver.20201001 Ends
		frappe.throw(str(self.leave_type))
		if not frappe.db.get_value("Leave Type", self.leave_type, 'allow_encashment'):
			frappe.throw(_("Leave Type {0} is not encashable").format(self.leave_type))

		allocation = self.get_leave_allocation()
		if not allocation:
			frappe.throw(_("No Leaves Allocated to Employee: {0} for Leave Type: {1}").format(self.employee, self.leave_type))

		# Ver.20201001 Begins, by SHIV on 2020/10/01
		# Following code commented by SHIV as the calculation is wrong
		'''
		self.leave_balance = allocation.total_leaves_allocated - allocation.carry_forwarded_leaves_count\
			- get_unused_leaves(self.employee, self.leave_type, allocation.from_date, self.encashment_date)
		'''

		# Following code added as a replacement for the above code
		self.leave_balance = get_leave_balance_on(employee=self.employee, date=today(), \
			to_date=today(), leave_type=self.leave_type, consider_all_leaves_in_the_allocation_period=True)

		if not self.employee_group:
			self.employee_group = frappe.db.get_value("Employee", self.employee, "employee_group")
		
		employee_group = frappe.get_doc("Employee Group", self.employee_group)
		# noof_encashments, encashment_days  = get_encashment_details(self.leave_period, self.employee)
		noof_encashments, encashment_days  = self.get_encashment_details()
  
		if flt(employee_group.max_encashment_days):
			encashable_days = flt(employee_group.max_encashment_days)-flt(encashment_days)
			encashable_days = encashable_days if encashable_days > 0 else 0
		else:
			encashable_days = 0
			frappe.throw(_("Maximum no.of days entitled for Encashment is not defined for Employee Group {}").format(self.employee_group))
   
		self.encashable_days = encashable_days
  
		if flt(self.encashment_days) > flt(self.leave_balance):
			self.encashment_days = flt(self.leave_balance) if flt(self.leave_balance) < flt(self.encashable_days) else flt(self.encashable_days)

		if flt(noof_encashments) >= flt(employee_group.encashment_frequency):
			frappe.throw(_("You have already encashed {} times for the current fiscal year").format(flt(employee_group.encashment_frequency)), title="Not Permitted")  

		# frappe.throw(str(self.leave_balance))
		if flt(self.leave_balance) < flt(employee_group.encashment_min):
			frappe.throw(_("Minimum {} days leave balance required for encashment. Your current leave balance is {} days only.").format(employee_group.encashment_min, self.leave_balance))
		# Ver.20201001 Ends

		# Following line commented by SHIV on 2020/10/02
		#encashable_days = self.leave_balance - frappe.db.get_value('Leave Type', self.leave_type, 'encashment_threshold_days')
		# self.encashable_days = encashable_days if encashable_days > 0 else 0

		# Ver.20201001 Begins, by SHIV on 2020/10/01
		# Following code commented 
		'''
		per_day_encashment = frappe.db.get_value('Salary Structure', salary_structure , 'leave_encashment_amount_per_day')
		self.encashment_amount = self.encashable_days * per_day_encashment if per_day_encashment > 0 else 0
		'''

		# Following code added by SHIV on 2020/10/02
		pay = get_basic_and_gross_pay(employee=self.employee, effective_date=today())
		if employee_group.leave_encashment_type == "Flat Amount":
			self.flat_amount	   	= flt(employee_group.leave_encashment_amount)
			self.encashment_amount 	= flt(employee_group.leave_encashment_amount)
		elif employee_group.leave_encashment_type == "Basic Pay":
			self.basic_pay			= flt(pay.get("basic_pay"))
			self.encashment_amount 	= (flt(pay.get("basic_pay"))/30)*flt(self.encashment_days)
		elif employee_group.leave_encashment_type == "Gross Pay":
			self.gross_pay			= flt(pay.get("gross_pay"))
			self.encashment_amount 	= (flt(pay.get("gross_pay"))/30)*flt(self.encashment_days)
		else:
			self.encashment_amount = 0

		self.leave_encashment_type = employee_group.leave_encashment_type
		self.salary_structure = pay.get("name")
		self.encashment_tax = get_salary_tax(self.encashment_amount)
		self.payable_amount = flt(self.encashment_amount,2) - flt(self.encashment_tax,2)
		# Ver.20201001 Ends

		self.leave_allocation = allocation.name
		return True

	def get_leave_allocation(self):		
		leave_allocation = frappe.db.sql("""select name, to_date, total_leaves_allocated, carry_forwarded_leaves_count 
                                   	from `tabLeave Allocation` 
                                    where '{0}'
									between from_date and to_date 
         							and docstatus=1 
                					and leave_type='{1}'
									and employee= '{2}'""".format(self.encashment_date or getdate(nowdate()), self.leave_type, self.employee), as_dict=1) #nosec

		return leave_allocation[0] if leave_allocation else None

	def create_leave_ledger_entry(self, submit=True):
		args = frappe._dict(
			leaves=self.encashment_days*-1 if submit==True else self.encashment_days,
			from_date=self.encashment_date,
			to_date=self.encashment_date,
			is_carry_forward=0
		)
		create_leave_ledger_entry(self, args, submit)

		# create reverse entry for expired leaves
		to_date = self.get_leave_allocation().get('to_date')
		if to_date < getdate(nowdate()):
			args = frappe._dict(
				leaves=self.encashment_days*-1 if submit==True else self.encashment_days,
				from_date=to_date,
				to_date=to_date,
				is_carry_forward=0
			)
			create_leave_ledger_entry(self, args, submit)

	# Following method added by SHIV on 2020/10/02
	def post_accounts_entry(self):
		if not self.cost_center:
			frappe.throw("Setup Cost Center for employee in Employee Information")

		# expense_bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		expense_bank_account = frappe.db.get_single_value("HR Accounts Settings", "default_bank_account")
		if not expense_bank_account:
			frappe.throw("Setup Default Expense Bank Account in HR Accounts Settings")

		expense_account = frappe.db.get_single_value("HR Accounts Settings", "leave_encashment_account")
		if not expense_account:
			frappe.throw("Setup Leave Encashment Account in HR Accounts Settings")

		tax_account = frappe.db.get_single_value("HR Accounts Settings", "salary_tax_account")
		if not tax_account:
			frappe.throw("Setup Tax Account in HR Accounts Settings")

		if frappe.db.exists('Company', {'abbr': 'BTL'}):
			voucher_type = 'Journal Entry'
			naming_series = 'Journal Voucher'
		else:
			voucher_type = 'Bank Entry'
			naming_series = 'Bank Payment Voucher'

		# Journal Entry		
		je = frappe.new_doc("Journal Entry")
		je.flags.ignore_permissions = 1 
		je.title = 'Leave Encashment Payable - ' + str(self.employee_name) + "(" + str(self.employee) + ")"
		je.voucher_type = "Journal Entry"
		je.naming_series = "Journal Voucher"
		# je.voucher_type = voucher_type
		# je.naming_series = naming_series
		je.company = self.company
		je.branch = self.branch
		je.remark = 'Payment against Leave Encashment: ' + self.name
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
				# "business_activity": self.business_activity,
		})

		if flt(self.encashment_tax):
			je.append("accounts", {
					"account": tax_account,
					"credit_in_account_currency": flt(self.encashment_tax,2),
					"credit": flt(self.encashment_tax,2),
					"reference_type": "Leave Encashment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					# "business_activity": self.business_activity,
			})

		payable_account = frappe.db.get_single_value("HR Accounts Settings", "salary_payable_account") #Added by Thukten
		if flt(self.payable_amount) > 0:
			je.append("accounts", {
					"account": payable_account,
					"reference_type": "Leave Encashment",
					"reference_name": self.name,
					"cost_center": self.cost_center,
					"credit_in_account_currency": flt(self.payable_amount,2),
					"credit": flt(self.payable_amount,2),
					# "business_activity": self.business_activity,
					"party_type": "Employee",
					"party": self.employee,
				})
		je.insert()
		je.submit()

		je_references = str(je.name)

		if flt(self.payable_amount) > 0:
			jeb_branch = frappe.db.get_single_value("HR Accounts Settings", "le_payment_branch")
			jeb = frappe.new_doc("Journal Entry")
			jeb.flags.ignore_permissions = 1
			jeb.title = "Leave Encashment Payment(" + self.employee_name + "  " + self.name + ")"
			jeb.voucher_type = "Bank Entry"
			jeb.naming_series = "Bank Payment Voucher"
			jeb.remark = 'Payment against Leave Encashment : ' + self.name
			jeb.user_remark = 'Payment against Leave Encashment: ' + self.name
			jeb.posting_date = today()
			jeb.branch = frappe.db.get_single_value("HR Accounts Settings","le_payment_branch")
			jeb_cost_center = frappe.db.get_value("Branch", jeb.branch, "cost_center")
			jeb.append("accounts", {
					"account": payable_account,
					"reference_type": "Journal Entry",
					"reference_name": je.name,
					"cost_center": self.cost_center,
					"debit_in_account_currency": self.payable_amount,
					"debit": self.payable_amount,
					# "business_activity": self.business_activity,
					"party_type": "Employee",
					"party": self.employee
				})

			jeb.append("accounts", {
					"account": expense_bank_account,
					"cost_center": jeb_cost_center,
					"reference_type": "Leave Encashment",
					"reference_name": self.name,
					"credit_in_account_currency": self.payable_amount,
					"credit": self.payable_amount,
					# "business_activity": self.business_activity,
				})
			jeb.insert()

			je_references = je_references + ", "+ str(jeb.name)
		#----Tax JE
		# if flt(self.encashment_tax)>0:
		# 	jet = frappe.new_doc("Journal Entry")
		# 	jet.flags.ignore_permissions = 1
		# 	jet.title =  "Employee Benefits Tax(" + str(self.employee_name) + ": " + self.name + ")"
		# 	jet.voucher_type = "Bank Entry"
		# 	jet.naming_series = "Bank Payment Voucher"
		# 	jet.remark = 'Beneift Tax against : ' + self.name
		# 	jet.posting_date = today()
		# 	jet.branch = self.branch
		# 	jet.append("accounts", {
		# 			"account": tax_account,
		# 			"cost_center": self.cost_center,
		# 			"debit_in_account_currency": flt(self.encashment_tax),
		# 			"debit": flt(self.encashment_tax),
		# 			"reference_type": "Journal Entry",
		# 			"reference_name": je.name,
		# 			"business_activity": self.business_activity,
		# 			"party_check":0
		# 	})
		# 	jet.append("accounts", {
		# 			"account": expense_bank_account,
		# 			"cost_center": self.cost_center,
		# 			"credit_in_account_currency": flt(self.encashment_tax),
		# 			"credit": flt(self.encashment_tax),
		# 			"business_activity": self.business_activity,
		# 			"reference_type": self.doctype,
		# 			"reference_name": self.name,
		# 	})
		# 	jet.insert()

		# 	je_references = je_references + ", "+ str(jet.name)

		self.db_set("journal_entry", je_references)

# # following method added by SHIV on 2021/05/04
# def get_encashment_details(leave_period, employee):
#     return frappe.db.sql("""SELECT IFNULL(COUNT(*),0) noof_encashments, IFNULL(SUM(encashment_days),0)
#                     FROM `tabLeave Encashment`
#                     WHERE leave_period = '{}'
#                     AND employee = '{}'
#                     AND docstatus != 2  
#                 """.format(leave_period, employee))[0]

	# following method added by SHIV on 2021/05/04
	def get_encashment_details(self):
		return frappe.db.sql("""SELECT IFNULL(COUNT(*),0) noof_encashments, IFNULL(SUM(encashment_days),0)
						FROM `tabLeave Encashment`
						WHERE leave_period = '{}'
						AND employee = '{}'
						AND name != '{}'
						AND docstatus != 2
						AND workflow_state not in ("Rejected")
					""".format(self.leave_period, self.employee, self.name))[0]

def create_leave_encashment(leave_allocation):
	''' Creates leave encashment for the given allocations '''
	for allocation in leave_allocation:
		if not get_assigned_salary_structure(allocation.employee, allocation.to_date):
			continue
		leave_encashment = frappe.get_doc(dict(
			doctype="Leave Encashment",
			leave_period=allocation.leave_period,
			employee=allocation.employee,
			leave_type=allocation.leave_type,
			encashment_date=allocation.to_date
		))
		leave_encashment.insert(ignore_permissions=True)

# Following code added by SHIV on 2020/010/02
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)
 
	# emp=frappe.db.sql('''
    #            select employee from `tabEmployee` where user_id='{0}'
    #            '''.format(user)
	# )
	

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return
	# employee = emp[0][0]
	return """(
		`tabLeave Encashment Request`.employee = '{employee}' and `tabLeave Encashment Request`.docstatus not in (1, 2) 
	)""".format(employee=frappe.db.get_value("Employee", {"user_id": user}, "name"))
   