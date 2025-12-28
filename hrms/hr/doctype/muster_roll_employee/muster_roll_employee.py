# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
from imaplib import Int2AP

import frappe
from frappe.model.document import Document

from frappe import _, whitelist
from frappe.model.document import Document
from frappe.utils import flt, getdate, cint, validate_email_address, today, add_years, date_diff, nowdate
from frappe.utils.data import get_first_day, get_last_day, add_days


class MusterRollEmployee(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.projects.doctype.musterroll.musterroll import Musterroll
		from erpnext.setup.doctype.employee_internal_work_history.employee_internal_work_history import EmployeeInternalWorkHistory
		from frappe.types import DF
		from hrms.hr.doctype.wages_history.wages_history import WagesHistory

		account_no: DF.Data | None
		amount: DF.Currency
		bank: DF.Link | None
		bank_account_type: DF.Link | None
		bank_branch: DF.Link | None
		blood_group: DF.Link | None
		branch: DF.Link | None
		company: DF.Link
		cost_center: DF.Link | None
		date_of_transfer: DF.Date | None
		designation: DF.Data | None
		gender: DF.Literal["Male", "Female", "Other"]
		id_card: DF.Data
		internal_work_history: DF.Table[EmployeeInternalWorkHistory]
		joining_date: DF.Date
		list_in_job_card: DF.Check
		mess_deduction: DF.Check
		mobile: DF.Data | None
		mr_type: DF.Literal["", "Under Labour Contract"]
		musterroll: DF.Table[Musterroll]
		person_name: DF.Data
		project: DF.Link | None
		qualification: DF.Data | None
		rate_per_day: DF.Currency
		rate_per_hour: DF.Currency
		rate_per_hour_normal: DF.Currency
		reference_docname: DF.Data | None
		reference_doctype: DF.Data | None
		salary: DF.Currency
		separation_date: DF.Date | None
		status: DF.Literal["Active", "Left"]
		temp_docname: DF.Data | None
		temp_doctype: DF.Data | None
		unit: DF.Link | None
		update_wage_history: DF.Check
		user_id: DF.Link | None
		wage_history: DF.Table[WagesHistory]
	# end: auto-generated types
	def validate(self):
		self.cal_rates()
		if len(self.musterroll) > 1:
			for a in range(len(self.musterroll)-1):
				self.musterroll[a].to_date = frappe.utils.data.add_days(getdate(self.musterroll[a + 1].from_date), -1)
		self.check_status()
		self.populate_work_history()
		# self.update_user_permissions()
		if self.update_wage_history:
			self.get_wage_history()

	def update_user_permissions(self):
		prev_branch  = self.get_db_value("branch")
		prev_company = self.get_db_value("company")
		prev_user_id = self.get_db_value("user_id")

		if prev_user_id:
			frappe.permissions.remove_user_permission("Muster Roll Employee", self.name, prev_user_id)
			frappe.permissions.remove_user_permission("Company", prev_company, prev_user_id)
			frappe.permissions.remove_user_permission("Branch", prev_branch, prev_user_id)

		if self.user_id:
			frappe.permissions.add_user_permission("Muster Roll Employee", self.name, self.user_id)
			frappe.permissions.add_user_permission("Company", self.company, self.user_id)
			frappe.permissions.add_user_permission("Branch", self.branch, self.user_id)
		
	def cal_rates(self):
		for a in self.get('musterroll'):
			if a.rate_per_day:
				a.rate_per_hour = flt(a.rate_per_day * 1.5) / 8
				a.rate_per_hour_normal = flt(a.rate_per_day) / 8

	def check_status(self):
		if self.status == "Left" and self.separation_date:
			self.docstatus = 1

	# Following method introducted by SHIV on 04/10/2017
	def populate_work_history(self):		
		if self.is_new() or len(self.internal_work_history) == 0:
			self.append("internal_work_history",{
						"branch": self.branch,
						"cost_center": self.cost_center,
						"from_date": self.joining_date,
						"owner": frappe.session.user,
						"creation": nowdate(),
						"modified_by": frappe.session.user,
						"modified": nowdate(),
						"reference_doctype": self.temp_doctype,
						"reference_docname": self.temp_docname
			})
		else:
			# Fetching previous document from db
			prev_doc = frappe.get_doc(self.doctype,self.name)
			self.date_of_transfer = self.date_of_transfer if self.date_of_transfer else today()
			if (getdate(self.joining_date) != prev_doc.joining_date) or \
			   (self.status == 'Left' and self.separation_date) or \
			   (self.cost_center != prev_doc.cost_center):
				for idx, wh in enumerate(self.internal_work_history):
					if (getdate(self.joining_date) != prev_doc.joining_date):
						if (
							idx == len(self.internal_work_history) - 1 and
							idx != 0 and
							wh.to_date is None and
							(getdate(prev_doc.joining_date) == getdate(wh.from_date)) and
							all(getdate(wh2.from_date) != getdate(self.joining_date) for i2, wh2 in enumerate(self.internal_work_history) if i2 < idx and i2 != 0)
						):
							wh.from_date = self.joining_date
					if (self.status == 'Left' and self.separation_date):
						if not wh.to_date:
							wh.to_date = self.separation_date
							if wh.from_date > wh.to_date:
								frappe.throw("To date cannot be before From Date (Separation Date)")
					elif prev_doc.separation_date:
						if (getdate(prev_doc.separation_date) == getdate(wh.to_date)):
							wh.to_date = self.separation_date
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
					"reference_doctype": self.temp_doctype,
					"reference_docname": self.temp_docname
			})
	#added by cety
	def get_wage_history(self):
		rate = 0
		from_date = ''
		to_date = ''
		for rate1 in self.musterroll:
			rate = rate1.rate_per_day
			from_date = rate1.from_date
			to_date = rate1.to_date
		
		date = nowdate()
		self.append("wage_history", {
			"modified_by1": frappe.session.user,
			"on_date": date,
			"rate_per_day": rate,
			"from_date": from_date,
			"to_date": to_date
		})


@frappe.whitelist()
def rejoin_muster_roll_employee(docname):
	doc = frappe.get_doc("Muster Roll Employee", docname)
	if doc.docstatus != 1 or doc.status != "Left":
		frappe.throw("Only submitted and 'Left' employees can be rejoined.")
	frappe.db.sql("""
		update `tabMuster Roll Employee` set docstatus=0, status='Active', separation_date=NULL where name=%s
	""", (docname,))
	return "Employee rejoined, status set to Active and docstatus set to Draft."
