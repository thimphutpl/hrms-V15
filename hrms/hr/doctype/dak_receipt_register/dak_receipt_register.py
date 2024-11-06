# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class DAKReceiptRegister(Document):
	def validate(self):
		self.check_action()
		
	def on_submit(self):
		pass

	def check_action(self):
		action = frappe.request.form.get('action')
		if self.workflow_state=="Waiting AFD Review" and action=="Forward":
			afd_head=frappe.get_value("Overall Settings", "afd_head")
			if afd_head!=frappe.session.user:
				frappe.throw("Only AFD can forward the Document")
		if action != "save":
			self.send_notification()
  
	def send_notification(self):
		action = frappe.request.form.get('action')  
		
		if action == "Apply":
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

