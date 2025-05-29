# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate, cint,today, add_years, date_diff, nowdate
from frappe.utils.data import get_first_day, get_last_day, add_days
from frappe.model.naming import set_name_by_naming_series, make_autoname
# from hrms.hr.hr_custom_functions import post_earned_leaves
class DFGANDGFG(Document):
	# def autoname(self):
	# 	if self.old_id:
	# 		self.employee = self.name = self.old_id	
	# 	if not self.date_of_joining:
	# 		frappe.throw("Date of Joining is required to generate the Employee ID.")
		
	# 	year = str(getdate(self.date_of_joining).year)[2:]
	# 	name = make_autoname(f'{self.employee_type}.{year}.#####')
	# 	self.employee = self.name = name
		
	def autoname(self):
		if self.old_id:
			self.employee = self.name = self.old_id
			return

		if not self.date_of_joining:
			frappe.throw("Date of Joining is required to generate the Employee ID.")

		if not self.employee_type:
			frappe.throw("Employee Type is required to generate the Employee ID.")

		year = str(getdate(self.date_of_joining).year)[2:]
		name = make_autoname(f'{self.employee_type}.{year}.#####')
		self.name = name
	
	def validate(self):
		# post_earned_leaves()
		self.check_status()
		self.calculate_rates()
		self.validate_block_listed()
		self.populate_work_history()

	def calculate_rates(self):
		# if not self.rate_per_day:
		self.rate_per_day = flt(self.salary) / 30
		self.rate_per_hour =(flt(self.salary) / 30) / 24
		gratuity_percent = frappe.db.get_value("HR Settings", None, "gratuity_percent")
		self.gratuity_fund = flt(gratuity_percent)/100  * flt(self.salary)

	def check_status(self):
		if self.status == "Left" and self.date_of_separation:
			self.docstatus = 1
	def validate_block_listed(self):
		block_listed_transaction = frappe.db.get_value("DFG AND GFG",{"id_card":self.id_card},"name")
		if block_listed_transaction:
			if frappe.db.get_value("DFG AND GFG",block_listed_transaction,"status")=="Active":
				if block_listed_transaction != self.name:
					frappe.throw("This CID is already registered with DFG AND GFG ID {id}".format(id=block_listed_transaction))
			else:
				black_listed = frappe.db.get_value("DFG AND GFG", block_listed_transaction, "black_listed")
				if black_listed:
					frappe.throw("This Desuup OR Gyalsup has been Black listed")
	
	# Following method introducted by SHIV on 04/10/2017
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

@frappe.whitelist()
def rejoin_dfg_gfg(docname):
	doc = frappe.get_doc("DFG AND GFG", docname)
	if doc.docstatus != 1 or doc.status != "Left":
		frappe.throw("Only submitted and 'Left' employees can be rejoined.")
	frappe.db.sql("""
		update `tabDFG AND GFG` set docstatus=0, status='Active', date_of_separation=NULL where name=%s
	""", (docname,))
	return "Employee rejoined, status set to Active and docstatus set to Draft."
