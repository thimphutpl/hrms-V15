# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
	add_days,
	cint,
	cstr,
	format_date,
	get_datetime,
	get_link_to_form,
	getdate,
	nowdate,
)

class DAKReceiptRegister(Document):
	def validate(self):
		self.check_action()
		self.update_dak_remark()
		
	def on_submit(self):
		pass

	

	def check_action(self):
		
		action = frappe.request.form.get('action')
		if self.workflow_state=="Waiting AFD Review" and action=="Forward":
			afd_head=frappe.get_value("Overall Settings", "afd_head")
			if afd_head!=frappe.session.user:
				frappe.throw("Only AFD can forward the Document")
		# frappe.throw(str(self.get_db_value("workflow_state")))
		if self.get_db_value("workflow_state")=="Pending":
			forward_to = frappe.db.sql('''
                               select forwarded_to from `tabDAK Remark` where parent="{}" order by creation DESC limit 1;
                               '''.format(self.name), as_dict=True)
			# frappe.throw(str(forward_to[0].get('forwarded_to')))
			user = frappe.get_value("Employee",forward_to[0].get('forwarded_to'),'user_id')
			if not user:
				frappe.throw("Please set user id for employee {}".format(user))
			
			if frappe.session.user != user:
				frappe.throw("Only {} can Submit or Reject as it was forwarded to him".format(user))
		if action != "save":
			self.send_notification()
   
	def update_dak_remark(self):
		user=""
		emp=""
		emp_name=""
		design=""
		action = frappe.request.form.get('action')
		user=frappe.session.user
		if not user:
			frappe.throw("You are using without session")
		emp=frappe.db.sql("select name from `tabEmployee` where user_id='{}'".format(user))
		if not emp:
			frappe.throw("You Cannot Apply If you are not an Employee")
   
		if action in ("Apply","Forward", "Receive", "Reject"):
			emp_name=frappe.db.get_value('Employee', emp, 'employee_name')
			design=frappe.db.get_value('Employee', emp, 'designation')
			self.append("items",{
				'user': user,
				'employee': emp,
				'employee_name':emp_name,
				'designation': design,
				'action': action,
				'remark_date': getdate(nowdate()),
				'remark': self.remark,
				'forwarded_to': self.employee if action in ("Forward") else ''
			})
   
			self.remark=""
   
	def send_notification(self):
		action = frappe.request.form.get('action')  
		
		if action == "Apply":
			self.employee=""
			self.employee_name=""
			self.forward_id=""
			self.notify_afd_head()
			self.notify_employee()
   
		elif action == "Forward":
			if not self.employee:
				frappe.throw("You have not set whom to forward")
			self.notify_forward_to()
			self.notify_employee()
   
		elif action != "Save":
			self.notify_employee()
   
	def notify_afd_head(self):
		self.doc = self
		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()

		args.update({
			"workflow_state": self.doc.workflow_state
		})
		afd_head=frappe.get_value("Overall Settings", "afd_head")
		try:
			email_template = frappe.get_doc("Email Template", 'DAK Receipt Notification')
			message = frappe.render_template(email_template.response, args)
			recipients = afd_head
			subject = email_template.subject
			self.send_mail(recipients, message, subject)
		except :
			frappe.msgprint(_("DAK Receipt Notification is missing."))
	
	def notify_employee(self):
		self.doc = self
		parent_doc = frappe.get_doc(self.doc.doctype, self.doc.name)
		args = parent_doc.as_dict()
		args.update({
			"workflow_state": self.doc.workflow_state
		})
		
		try:
			email_template = frappe.get_doc("Email Template", 'DAK Receipt Status Notification')
			message = frappe.render_template(email_template.response, args)
			recipients = self.doc.owner
			subject = email_template.subject
			self.send_mail(recipients, message, subject)
		except :
			frappe.msgprint(_("DAK Receipt Status Notification is missing."))
		
	def notify_forward_to(self):
		
		parent_doc = frappe.get_doc(self.doctype, self.name)
		args = parent_doc.as_dict()
		
		try:
			email_template = frappe.get_doc("Email Template", "DAK Receipt Forwarded Notification")
			message = frappe.render_template(email_template.response, args)
			subject = email_template.subject
			self.send_mail(self.forward_id,message,subject)
		except :
			frappe.msgprint(_("DAK Receipt Forwarded Notification."))
		
	   
	
	def send_mail(self, recipients, message, subject):
		
		frappe.sendmail(
				recipients=recipients,
				subject=_(subject),
				message= _(message),
				
			)

