# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SemsoEntry(Document):
	def validate(self):
		self.total_validate()
	def total_validate(self):
		total_employees = len(self.semso_contribution)
		# If amount is per row and you want to multiply each by total_employees
		for row in self.semso_contribution:
			row.amount = self.amount * total_employees

	
			
		  

@frappe.whitelist()
def get_employee(company=None, troops=None,officers=None):
	if not company:
		frappe.throw("Company is required")
	types_list = []
	if troops and str(troops) in ["1", "True", "true", 1, True]:
		types_list.append("Troops")
	if officers and str(officers) in ["1", "True", "true", 1, True]:
		types_list.append("Officer")
   

	parents = frappe.get_all(
		"Semso Deduction Group",
		filters={
			"company": company,
			"semso_type": ["in", types_list]
		},
		pluck="name"
	)
	grades = frappe.get_all(
		"Semso Item",  # ⚠️ change to your child table name
		filters={
			"parent": ["in", parents]
		},
		pluck="grade"
	)
   
	if not grades:
		return []

	# Step 2: Get employees based on grades
	employees = frappe.get_all(
		"Employee",
		filters={
			"company": company,
			"grade": ["in", grades],
			"status": "Active"
		},
		fields=["name", "employee_name", "grade"]
	)
   

	return employees