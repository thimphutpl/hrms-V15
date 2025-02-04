# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, cint, today, add_years, date_diff, nowdate
from frappe.utils.data import get_first_day, get_last_day, add_days
from frappe.model.naming import make_autoname

class Operator(Document):
	def autoname(self):
		if self.old_id:
			self.name = self.old_id
			return
		else:
			series = 'OPP'
			self.name = make_autoname(str(series) + ".YY.MM.###")

	def validate(self):
		self.populate_work_history()
		self.check_status()
	def check_status(self):
		if self.status == "Left" and self.date_of_separation:
			self.docstatus = 1

	def populate_work_history(self):
		if not self.internal_work_history:
			self.append("internal_work_history",{
				"branch": self.branch,
				"reference_doctype": self.doctype,
				"reference_docname": self.name,
				"from_date": self.date_of_joining
		})
		else:
	# Fetching previous document from db
			for wh in self.internal_work_history:
				# For change in date_of_joining
				if self.date_of_transfer and self.status !='Left':
					if (getdate(self.date_of_joining) == getdate(wh.from_date)):
						if self.status == 'Left' and not self.date_of_separation:
							frappe.throw("Date of separation is required for status left")
						elif self.status== 'Left' and self.date_of_separation:
							wh.branch=self.branch
							wh.to_date = self.date_of_separation
						elif self.date_of_transfer:
							if getdate(self.date_of_transfer) < getdate(wh.from_date):
								frappe.throw("Date of transfer can not be before joining date")
							wh.to_date = self.date_of_transfer
						# For change in date_of_separation, cost_center	
						if getdate(self.date_of_transfer) > getdate(today()):
							frappe.throw(_("Date of transfer cannot be a future date."),title="Invalid Date")      
				else:
					if (getdate(self.date_of_transfer) == getdate(wh.from_date)):
						if self.status == 'Left' and not self.date_of_separation:
							frappe.throw("Date of separation is required for status left")
						elif self.status== 'Left' and self.date_of_separation:
							wh.branch=self.branch
							wh.to_date = self.date_of_separation

			if (self.date_of_transfer and self.status !='Left'):
				self.append("internal_work_history",{
					"branch": self.branch,
					"from_date": self.date_of_transfer,
					"reference_doctype": self.doctype,
					"reference_docname": self.name,
			})

