# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate



class AttendanceOthers(Document):
	def validate(self):
		if self.date:
			if self.date > nowdate():
				frappe.throw("Cannot Take Attendance For Future Date")