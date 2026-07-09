# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class SemsoEntry(Document):
	def validate(self):
		self.calculate_total()

	def calculate_total(self):
		count = len(self.deceased)
	
		for item in self.semso_contribution:
			base_amount = item.base_amount
			if self.spouse_semso:
				item.amount = (base_amount*count)/2
			else:
				item.amount = (base_amount*count)
	
			


@frappe.whitelist()
def get_employee(company=None, semso_contributor=None):

	if not company:
		frappe.throw("Company is required")

	if not semso_contributor:
		return []

	# FIX: convert string to list if needed
	if isinstance(semso_contributor, str):
		semso_contributor = json.loads(semso_contributor)


	employee_groups = []
	use_grade = False
	use_group = False

	for row in semso_contributor:

		contribution = row.get("semso_contribution")

		if row.get("employee_group") == 1:
			employee_groups.append(contribution)
			use_group = True

		if row.get("employee_grade") == 1:
			employee_groups.append(contribution)
			use_grade = True



	group_names = []
	if employee_groups:
		group_names = frappe.get_all(
			"Employee Group Master",
			filters={
				"company": company,
				"name": ["in",employee_groups]
			},
			pluck="name"
		)

	if not group_names:
		group_names = []

	# -----------------------------
	# 3. Get Grades from Master Items
	# -----------------------------
	grades = []
	if group_names:
		grades = frappe.get_all(
			"Employee Group Master Item",
			filters={
				"parent": ["in", group_names]
			},
			pluck="grade"
		)

	# merge grade filters from direct selection + master
	all_grades = list(set(grades))
	

	if not all_grades:
		return []

	employees = frappe.get_all(
		"Employee",
		filters={
			"company": company,
			"grade": ["in", all_grades],
			"status": "Active"
		},
		fields=[
			"name",
			"employee_name",
			"grade",
			"employee_group"
		]
	)
	for emp in employees:

	
		grade_amount = 0
		group_amount = 0

	
		if use_grade:
			grade_result =frappe.db.sql("""
							SELECT egm.amount
							FROM `tabSemso Deduction Master` sdm 
							JOIN `tabSemso Employee Grade` egm 
							   ON sdm.name = egm.parent
							WHERE sdm.company = %s AND egm.employee_grade = %s	
							""",(company,emp.grade),as_dict=1)
			grade_amount = grade_result[0].amount if grade_result else 0
		if use_group:

			if not isinstance(employee_groups, list):
				employee_groups = [employee_groups]
			
	
			if not isinstance(emp.grade, list):
				grades = [emp.grade]
			else:
				grades = emp.grade
			

			group_placeholders = ', '.join(['%s'] * len(employee_groups))
			grade_placeholders = ', '.join(['%s'] * len(grades))
			
			query = f"""
				SELECT sdm.amount, seg.grade
				FROM `tabSemso Deduction Master` sdm
				JOIN `tabEmployee Group Master` egm 
					ON sdm.emp_group = egm.name
				JOIN `tabEmployee Group Master Item` seg 
					ON egm.name = seg.parent
				WHERE sdm.emp_group IN ({group_placeholders})
					AND seg.grade IN ({grade_placeholders})
					AND sdm.company = %s
			"""
			
			params = employee_groups + grades + [company]
			result = frappe.db.sql(query, params, as_dict=1)
	

			group_amount = result[0].amount if result else 0
			

		emp.grade_amount = grade_amount
		emp.group_amount = group_amount
		emp.amount = (grade_amount or 0) + (group_amount or 0)

	return employees