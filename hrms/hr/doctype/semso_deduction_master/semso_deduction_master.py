# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SemsoDeductionMaster(Document):
	def validate(self):
		self.vaildate_employee_group()
	def vaildate_employee_group(self):
		doc=frappe.db.sql("""
			SELECT egmi.name  FROM `tabEmployee Group Master` egm 
					JOIN `tabEmployee Group Master Item` egmi 
					ON egm.name=egmi.parent 
					WHERE egm.name=%s

			""",(self.emp_group),as_dict=1)
		if not doc:
			frappe.throw("Please set Employee Group Master first")
@frappe.whitelist()
def get_all_employee_group(employee_group=None):
	doc = frappe.db.sql("""
			SELECT egmi.grade  FROM `tabEmployee Group Master` egm 
			JOIN `tabEmployee Group Master Item` egmi 
			ON egm.name=egmi.parent 
			WHERE egm.name=%s""",(employee_group),as_dict=1
		)
	return doc