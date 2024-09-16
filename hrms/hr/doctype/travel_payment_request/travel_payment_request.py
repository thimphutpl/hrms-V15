# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from frappe import _
import frappe
from frappe.model.document import Document


class TravelPaymentRequest(Document):
	def validate(self):
		self.validate_employees()

	def on_submit(self):
		self.post_abstract_bill()

	def validate_employees(self):
		for item in self.items:
			employee_id = item.employee
			
			# Query existing Travel Payment Request records for the same date range and employee
			duplicate_records = frappe.db.sql("""
				SELECT 
					parent 
				FROM 
					`tabTravel Payment Request Item` 
				WHERE 
					employee = %s 
					AND parent != %s
					AND EXISTS (
						SELECT 1 
						FROM `tabTravel Payment Request` 
						WHERE 
							name = parent 
							AND ((from_date BETWEEN %s AND %s) 
								OR (to_date BETWEEN %s AND %s) 
								OR (%s BETWEEN from_date AND to_date) 
								OR (%s BETWEEN from_date AND to_date))
					)
			""", (employee_id, self.name, self.from_date, self.to_date, self.from_date, self.to_date, self.from_date, self.to_date))

			# If duplicates are found, raise a validation error
			if duplicate_records:
				frappe.throw(_("Employee {0} has already been assigned a travel payment request within the selected date range.").format(employee_id))

	def post_abstract_bill(self):
		account = frappe.db.get_value("Company", self.company, "travel_expense_account")
		if not account:
			frappe.throw("Please set account")
		items = []
		items.append({
			"account": account,
			"cost_center": self.cost_center,
			"party_type": "Employee",
			"party": self.employee,
			"business_activity": self.business_activity,
			"amount": self.total_amount,
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
