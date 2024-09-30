# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import frappe
from frappe import _
from frappe.utils import flt, cint, nowdate, getdate, formatdate, money_in_words
from frappe.model.document import Document


class TravelPaymentRequest(Document):
	def validate(self):
		self.validate_duplicate_employees()

	def on_submit(self):
		self.post_abstract_bill()

	def before_cancel(self):
		if self.abstract_bill:
			ab_status = frappe.get_value("Abstract Bill", {"name": self.abstract_bill}, "docstatus")
			if cint(ab_status) == 1:
				frappe.throw("Abstract Bill {} for this transaction needs to be cancelled first".format(frappe.get_desk_link("Abstract Bill", self.abstract_bill)))
			else:
				frappe.db.sql("delete from `tabAbstract Bill` where name = '{}'".format(self.abstract_bill))
				self.db_set("abstract_bill", None)

	def validate_duplicate_employees(self):
		for item in self.items:
			# SQL query to check for duplicate employees within the date range
			query = """
				SELECT t2.from_date, t2.to_date
				FROM `tabTravel Payment Request` t1, `tabTravel Payment Request Item` t2
				WHERE t1.name = t2.parent
				AND t2.employee = %(employee)s
				AND (
					(t2.from_date BETWEEN %(from_date)s AND %(to_date)s) 
					OR (t2.to_date BETWEEN %(from_date)s AND %(to_date)s) 
					OR (%(from_date)s BETWEEN t2.from_date AND t2.to_date) 
					OR (%(to_date)s BETWEEN t2.from_date AND t2.to_date)
				)  
				AND t1.docstatus IN (1)
			"""
			
			# Parameters to pass into the SQL query
			params = {
				'employee': item.employee,
				'from_date': item.from_date,
				'to_date': item.to_date
			}

			# Execute the query and fetch duplicate records
			duplicate_records = frappe.db.sql(query, params, as_dict=True)
		
			# If duplicates are found, raise a validation error
			if duplicate_records:
				from_date = duplicate_records[0]["from_date"]
				to_date = duplicate_records[0]["to_date"]
				frappe.throw(
					_("Employee {} has already been assigned a travel payment request within the selected date range between {} and {}.").format(
						frappe.bold(item.employee),
						frappe.bold(from_date),
						frappe.bold(to_date),
					)
				)	

	def post_abstract_bill(self):
		account = frappe.db.get_value("Company", self.company, "travel_expense_account")
		if not account:
			frappe.throw("Please set account")
		items = []
		for d in self.items:
			items.append({
				"account": account,
				"cost_center": self.cost_center,
				"party_type": "Employee",
				"party": d.employee,
				"business_activity": self.business_activity,
				"amount": d.amount,
			})		
		ab = frappe.new_doc("Abstract Bill")
		ab.flags.ignore_permission = 1
		ab.update({
			"doctype": "Abstract Bill",
			"posting_date": self.posting_date,
			"company": self.company,
			"branch": self.branch,
			"reference_doctype": self.doctype,
			"reference_name": self.name,
			"items": items,
		})
		ab.insert()
		self.db_set('abstract_bill', ab.name)
		frappe.msgprint(_('Abstarct Bill {0} posted').format(frappe.get_desk_link("Abstract Bill", ab.name)))


@frappe.whitelist()
def get_business_activities(doctype, txt, searchfield, start, page_len, filters):
	cond = ""
	if filters and filters.get("company"):
		cond = "and t2.company = %(company)s"

	return frappe.db.sql(
		f"""
		select t1.name 
		from `tabBusiness Activity` t1, `tabBusiness Activity Company` t2
		where t1.name = t2.parent and t1.`{searchfield}` LIKE %(txt)s {cond}
		order by t1.name 
		limit %(page_len)s offset %(start)s
		""",
		{
			"txt": "%" + txt + "%",
			"company": filters.get("company"),
			"start": start,
			"page_len": page_len
		}
	)