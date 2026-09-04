# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArmForce(Document):
	def validate(self):
		self.check_cid()
	
	def check_cid(self):
		old_cid=frappe.db.get_value("Arm Force",{"cid_no":self.cid_no},"name")
		if old_cid and old_cid != self.name:
			frappe.throw("This Arm Force with same CID already registered in "+ old_cid)