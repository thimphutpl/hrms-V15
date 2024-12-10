# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from datetime import datetime
from dateutil.relativedelta import relativedelta
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from erpnext.accounts.doctype.accounts_settings.accounts_settings import get_bank_account

class SWSApplication(Document):
	def validate(self):
		# validate_workflow_states(self)
		self.check_review()
		self.validate_dead()
		self.validate_amount()
		self.validate_workflow()


	def validate_workflow(self):
		action = frappe.request.form.get('action')
		reviewer_list=[reviewer.reviewer_id for reviewer in self.reviewer]
		user=frappe.db.get_value("Employee", self.employee, "user_id")

		if len(reviewer_list)==0:
			frappe.throw("Set the reviewer list sws setting")

		users = frappe.get_doc("User", frappe.session.user)
		user_roles = [d.role for d in users.roles]

		if action == "Apply":
			self.workflow_state="Waiting Supervisor Approval"

			self.notify_reviewers(user)
			self.notify_reviewers(self.supervisor)

		if action == "Forward to Verifier":
			if frappe.session.user != self.supervisor:
				frappe.throw("Only {} can forward to verifier".format(self.supervisor))

			self.workflow_state="Waiting SWS User Approval"

			self.notify_reviewers(user)
			self.notify_reviewers(reviewer_list)

		if action == "Forward to Approver":
			if frappe.session.user not in reviewer_list:
				frappe.throw("Only {} can forward to approver".format(",".join(reviewer_list)))
			self.review()
			if self.reviewed==0:
				self.workflow_state = "Waiting SWS User Approval"
			else:
				self.workflow_state = "Waiting Accounts Approval"
				self.notify_reviewers(user)

		if action == "Approve":
			if "Accounts User" not in user_roles:
				frappe.throw("Only Accounts User can approve")
			self.workflow_state="Approved"
			self.notify_reviewers(user)

		if action == "Reject":
			if ("Accounts User" not in user_roles) and (frappe.session.user not in reviewer_list) and (frappe.session.user!=self.supervisor):
				frappe.throw("You do not have permission to reject")
			self.workflow_state="Rejected"
			self.notify_reviewers(user)
			

		if action == "Reapply":
			self.reApply()
			self.workflow_state="Waiting Supervisor Approval"
			self.notify_reviewers(user)

	def review(self):
		user=frappe.session.user
		for reviewer in self.reviewer:
			if reviewer.reviewer_id==user:
				reviewer.reviewed=1
		self.check_review()


	def reApply(self):
		for reviewer in self.reviewer:
			reviewer.reviewed=0
			reviewer.remarks=""
		
	def notify_reviewers(self, recipients):
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		
		try:
			email_template = frappe.get_doc("Email Template", 'SWS Application Status Notification')
			message = frappe.render_template(email_template.response, args)
			subject = email_template.subject
			self.send_mail(recipients,message,subject)
		except :
			frappe.msgprint(_("Internal Audit Clearance notification is missing."))



	def send_mail(self, recipients, message, subject):
		frappe.sendmail(
				recipients=recipients,
				subject=_(subject),
				message= _(message),  
			)

	def validate_amount(self):
		total_amount = 0
		for a in self.items:
			if not a.amount:
				a.amount = a.claim_amount
			total_amount = flt(total_amount) + flt(a.amount)	
		self.total_amount = total_amount

	def validate_dead(self):
		for a in self.items:
			doc = frappe.get_doc("SWS Membership Item", a.select_item)
			if doc.deceased == 1:
				frappe.throw("The dependent is marked deceased in Membership and Employee Family Detail. Please contact HR Section")

	def on_submit(self):
		if self.total_amount <= 0:
			frappe.throw("Total Amount cannot be 0 or less")
		self.update_status()
		self.post_sws_contribution()
		self.post_sws_entry()
		# self.create_journal_entry()
		# added by Kinley Dorji 2021/06/11
		salary_structure = frappe.get_doc("Salary Structure",{"employee":self.employee,"is_active":'Yes'})
		salary_structure.save(ignore_permissions = True)

	def update_status(self,cancel =False):
		if cancel:
			frappe.throw("Cannot Update or Cancel, This Document is Linked With Journal Entry")
		for a in self.items:
			if frappe.db.get_value("SWS Event", a.sws_event, "deceased"):
				doc = frappe.get_doc("Employee Family Details", a.select_item)
				swsdoc = frappe.get_doc("SWS Membership Item", a.select_item)
				if self.docstatus == 1:
					doc.db_set("deceased", 1)
					swsdoc.db_set("deceased", 1)
				if self.docstatus == 2:
					doc.db_set("deceased", 0)
					swsdoc.db_set("deceased", 0)
			row = frappe.get_doc("SWS Membership Item", a.select_item)
			if self.docstatus == 1:
				row.status = 'Claimed'
				row.claim_amount = self.total_amount
				row.sws_application = self.name
			if self.docstatus == 2:
				row.status = 'Active'
				row.claim_amount = None
				row.sws_application = None
			row.save(ignore_permissions = True)

	def create_journal_entry(self):
		je = frappe.new_doc("Journal Entry")
		je_ref = ""
		je.flags.ignore_permissions = 1 
		cost_center = frappe.db.get_value("Branch",self.branch,"cost_center")
		expense_bank_account = get_bank_account(self.branch)
		je.update({
			"voucher_type": "Journal Entry",
			"naming_series": "Journal Voucher",
			"company": self.company,
			"remark": self.name,
			"posting_date": self.posting_date,
			"branch": self.branch
			})

		#credit account update
		je.append("accounts", {
			"account": self.credit_account,
			"credit_in_account_currency": self.total_amount,
			"reference_type": self.doctype,
			"reference_name": self.name,
			"cost_center": cost_center
			})
		#debit account update
		je.append("accounts", {
			"account": self.debit_account,
			"debit_in_account_currency": self.total_amount,
			"reference_type": self.doctype,
			"reference_name": self.name,
			"party_type": "Employee",
			"party": self.employee,
			"cost_center": cost_center
			})
		je.save(ignore_permissions = True)
		je.submit()
		je_ref = je.name
		jebp = frappe.new_doc("Journal Entry")
		jebp.flags.ignore_permissions = 1 
		cost_center = frappe.db.get_value("Branch",self.branch,"cost_center")
		jebp.update({
			"voucher_type": "Journal Entry",
			"naming_series": "Journal Voucher",
			"company": self.company,
			"remark": self.name,
			"posting_date": self.posting_date,
			"branch": self.branch
			})

		#credit account update
		jebp.append("accounts", {
			"account": expense_bank_account,
			"credit_in_account_currency": self.total_amount,
			"reference_type": self.doctype,
			"reference_name": self.name,
			"party_type": "Employee",
			"party": self.employee,
			"cost_center": cost_center
			})
		#debit account update
		jebp.append("accounts", {
			"account": self.credit_account,
			"debit_in_account_currency": self.total_amount,
			"reference_type": self.doctype,
			"reference_name": self.name,
			"party_type": "Employee",
			"party": self.employee,
			"cost_center": cost_center
			})
		jebp.insert()
		je_ref += ", "+jebp.name
		self.db_set("je_ref", je_ref)


	def post_sws_entry(self):
		doc = frappe.new_doc("SWS Entry")
		doc.flags.ignore_permissions = 1
		doc.posting_date = self.posting_date
		doc.branch = self.branch
		doc.ref_doc = self.name
		doc.company = self.company
		doc.employee = self.employee
		doc.debit = self.total_amount
		doc.submit()

	def post_sws_contribution(self, cancel=False):
		# sws = frappe.db.get_single_value("SWS Settings", "salary_component")
		amount = flt(self.total_amount,2)
		if not cancel:
			if not amount:
				return
			if not frappe.db.exists("SWS Contribution", {"employee": self.employee}):
				doc = frappe.new_doc("SWS Contribution")
				doc.flags.ignore_permissions = 1
				# doc.posting_date = nowdate()
				# doc.branch = self.branch
				doc.employee = self.employee
				doc.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
				row = doc.append("contributions", {})
				row.reference_type = "SWS Application"
				row.reference_name = self.name
				row.contribution_amount = -1*amount
				row.fiscal_year = str(self.posting_date).split("-")[0]
				row.month = str(self.posting_date).split("-")[1]
				doc.insert()
			else:
				sws_contribution = frappe.get_doc("SWS Contribution", {"employee": self.employee})
				row = sws_contribution.append("contributions", {})
				row.reference_type = "SWS Application"
				row.reference_name = self.name
				row.contribution_amount = -1*amount
				row.fiscal_year = str(self.posting_date).split("-")[0]
				row.month = str(self.posting_date).split("-")[1]
				sws_contribution.save()
		else:
			if frappe.db.exists("SWS Contribution", {"employee": self.employee}):
				doc = frappe.get_doc("SWS Contribution", {"employee": self.employee})
				for a in doc.contributions:
					if a.reference_name == self.name:
						doc.delete(a)
				doc.save(ignore_permissions=1)
				

	def before_cancel(self):
		self.reset_status()

	def on_cancel(self):
		self.update_status(cancel = True)
		self.post_sws_contribution(cancel=True)
		self.delete_sws_entry()

	def reset_status(self):
		self.verified = 0
		self.approval_status = None

	def delete_sws_entry(self):
		frappe.db.sql("delete from `tabSWS Entry` where ref_doc = %s", self.name)
	
	def check_review(self):
		review_count=0
		for reviewer in self.reviewer:
			if reviewer.reviewed==1:
				review_count+=1
		
		if len(self.reviewer)==review_count:
			self.reviewed=1
		
		if len(self.reviewer) == review_count-1:
			self.last_review=1

	@frappe.whitelist()
	def get_sws_accounts(self):
		credit_account = frappe.db.get_single_value("HR Accounts Settings", "sws_credit_account")
		debit_account = frappe.db.get_single_value("HR Accounts Settings", "sws_debit_account")
		return credit_account, debit_account
	
	@frappe.whitelist()
	def get_reviewers(self):
		if len(self.reviewer)==0:
			reviewers=frappe.db.sql("Select reviewer, reviewer_id, reviewer_name from `tabSWS Reviewer Setting Item` where parent='SWS Settings'", as_dict=True)
			# frappe.throw(str(reviewers))
			for reviewer in reviewers:
				self.append("reviewer",{
					"reviewer": reviewer.reviewer,
					"reviewer_id": reviewer.reviewer_id,
					"reviewer_name": reviewer.reviewer_name
				})
		sup=frappe.get_doc("Employee",frappe.db.get_value("Employee", self.employee, "reports_to"))
		self.supervisor=sup.user_id
		self.supervisor_name=sup.employee_name
		self.supervisor_designation=sup.designation
	
	@frappe.whitelist()
	def get_child_doc_names(self, parent_name):

		children=frappe.db.sql("select name from `tabSWS Membership Item` where parent='{}'".format(parent_name), as_dict=True)
		child_list=[ child.name for child in children]
		return child_list


	@frappe.whitelist()
	def get_member_details(self, name):
		if not name:
			frappe.msgprint("Please select Reference Document first")
		relationship = cid_no = full_name = None
		data =  frappe.db.sql("""
					   select relationship, cid_no, full_name from `tabSWS Membership Item` where name = '{}'
					   """.format(name),as_dict=1)
		if len(data) > 0:
			relationship = data[0].relationship
			cid_no = data[0].cid_no
			full_name = data[0].full_name
		return relationship, cid_no, full_name
	#filtering family members based on sws membership

@frappe.whitelist()
def filter_sws_member_item(doctype, txt, searchfield, start, page_len, filters):
	# frappe.throw("here")
	data = []
	if not filters.get("employee"):
		frappe.throw("Please select employee first.")
	return frappe.db.sql("""
	select a.name as name, a.full_name as full_name from `tabSWS Membership Item` a, `tabSWS Membership` b where a.parent = b.name
	and b.employee = '{0}' and a.status != 'Claimed' and b.docstatus = 1 and a.parentfield='members'
	""".format(filters.get("employee")))

@frappe.whitelist() 
def get_event_amount(sws_event, reference, employee):
	if not reference:
		frappe.throw("Please select Reference Document")
	parent_document = frappe.db.get_value("SWS Membership Item", reference, "parent")
	registration_date = frappe.db.get_value("SWS Membership", parent_document, "registration_date")
	d1 = datetime.strptime(str(registration_date),'%Y-%m-%d')
	d2 = datetime.strptime(frappe.utils.nowdate(), '%Y-%m-%d')
	date_diff = relativedelta(d2,d1).years
	# frappe.msgprint(str(date_diff))
	if date_diff <= 1:
		event_amount = frappe.db.sql("""
					select amount from `tabSWS Event Item` where parent = '{0}' and noof_years = 'Within 1 year'
							   """.format(sws_event), as_dict = True)
	elif date_diff > 1 and date_diff <= 2:
		event_amount = frappe.db.sql("""
					select amount from `tabSWS Event Item` where parent = '{0}' and noof_years = 'Within 2 years'
							   """.format(sws_event), as_dict = True)
	elif date_diff > 2 and date_diff <= 3:
		event_amount = frappe.db.sql("""
					select amount from `tabSWS Event Item` where parent = '{0}' and noof_years = 'Within 3 years'
							   """.format(sws_event), as_dict = True)
	elif date_diff > 3 and date_diff <= 4:
		event_amount = frappe.db.sql("""
					select amount from `tabSWS Event Item` where parent = '{0}' and noof_years = 'Within 4 years'
							   """.format(sws_event), as_dict = True)
	elif date_diff >= 5:
		event_amount = frappe.db.sql("""
					select amount from `tabSWS Event Item` where parent = '{0}' and noof_years = '5 years and above'
							   """.format(sws_event), as_dict = True)

	return event_amount

	

# Following code added by SHIV on 2020/09/21
def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabSWS Application`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabSWS Application`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabSWS Application`.supervisor = '{user}' and `tabSWS Application`.workflow_state != 'Draft')
	)""".format(user=user)

