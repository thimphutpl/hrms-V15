# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class SWSMembershipItem(Document):
	def autoname(self):
		# doc = frappe.get_doc("SWS Membership", self.parent)
		self.name = self.full_name+"-"+self.relationship+"-"+str(self.employee)
