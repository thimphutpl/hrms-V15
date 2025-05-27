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
		if self.is_new() or len(self.internal_work_history) == 0:
			self.append("internal_work_history",{
						"branch": self.branch,
						"cost_center": self.cost_center,
						"from_date": self.date_of_joining,
						"owner": frappe.session.user,
						"creation": nowdate(),
						"modified_by": frappe.session.user,
						"modified": nowdate(),
						
			})
		else:
			# Fetching previous document from db
			prev_doc = frappe.get_doc(self.doctype,self.name)
			self.date_of_transfer = self.date_of_transfer if self.date_of_transfer else today()
			if (getdate(self.date_of_joining) != prev_doc.date_of_joining) or \
			   (self.status == 'Left' and self.date_of_separation) or \
			   (self.cost_center != prev_doc.cost_center):
				for idx, wh in enumerate(self.internal_work_history):
					if (getdate(self.date_of_joining) != prev_doc.date_of_joining):
						if (
							idx == len(self.internal_work_history) - 1 and
							idx != 0 and
							wh.to_date is None and
							(getdate(prev_doc.date_of_joining) == getdate(wh.from_date)) and
							all(getdate(wh2.from_date) != getdate(self.date_of_joining) for i2, wh2 in enumerate(self.internal_work_history) if i2 < idx and i2 != 0)
						):
							wh.from_date = self.date_of_joining
					if (self.status == 'Left' and self.date_of_separation):
						if not wh.to_date:
							wh.to_date = self.date_of_separation
							if wh.from_date > wh.to_date:
								frappe.throw("To date cannot be before From Date (Separation Date)")
					elif prev_doc.date_of_separation:
						if (getdate(prev_doc.date_of_separation) == getdate(wh.to_date)):
							wh.to_date = self.date_of_separation
				if (self.cost_center != prev_doc.cost_center):
					if getdate(self.date_of_transfer) > getdate(today()):
						frappe.throw(_("Date of transfer cannot be a future date."),title="Invalid Date")      
					elif not wh.to_date:
						if getdate(self.date_of_transfer) < getdate(wh.from_date):
							frappe.throw(_("Row#{0} : Date of transfer({1}) cannot be beyond current effective entry.").format(wh.idx,self.date_of_transfer),title="Invalid Date")
						wh.to_date = wh.from_date if add_days(getdate(self.date_of_transfer),-1) < getdate(wh.from_date) else add_days(self.date_of_transfer,-1)
		if 'prev_doc' in locals() and ((self.cost_center != prev_doc.cost_center) or (prev_doc.status == 'Left' and self.status == 'Active')):
			self.append("internal_work_history",{
					"branch": self.branch,
					"cost_center": self.cost_center,
					"from_date": self.date_of_transfer,
					"owner": frappe.session.user,
					"creation": nowdate(),
					"modified_by": frappe.session.user,
					"modified": nowdate(),
					
			})
	#added by cety
				
@frappe.whitelist()
def rejoin_operator(docname):
	doc = frappe.get_doc("Operator", docname)
	if doc.docstatus != 1 or doc.status != "Left":
		frappe.throw("Only submitted and 'Left' employees can be rejoined.")
	frappe.db.sql("""
		update `tabOperator` set docstatus=0, status='Active', date_of_separation=NULL where name=%s
	""", (docname,))
	return "Employee rejoined, status set to Active and docstatus set to Draft."


