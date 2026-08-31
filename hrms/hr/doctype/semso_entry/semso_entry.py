# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json

class SemsoEntry(Document):
	def validate(self):
		self.calculate_total()
		self.semso_calculate_total()

	def calculate_total(self):
		for item in self.semso_contribution:
			base_amount = item.base_amount
			if self.spouse_semso:
				item.amount = (base_amount*self.number_of_people)/2
			else:
				item.amount = (base_amount*self.number_of_people)
	def semso_calculate_total(self):
		self.total_officer = 0
		self.total_troops = 0
		self.total_civilan = 0

		for row in self.semso_contribution:
			amount = row.amount or 0
			self.total_amount = (self.total_officer or 0) + (self.total_troops or 0) + (self.total_civilan or 0)

			if row.employee_group == "Officer (RBA)":
				self.total_officer += amount

			elif row.employee_group == "Troops (RBA)":
				self.total_troops += amount

			elif row.employee_group == "Civilian":
				self.total_civilan += amount
		
				
@frappe.whitelist()
def get_employee(employee_group, company=None, semso_contributor=None):

	if not company:
		frappe.throw("Company is required")

	if not employee_group:
		frappe.throw("Employee Group is required")

	# Convert child table JSON to Python list
	if isinstance(semso_contributor, str):
		semso_contributor = json.loads(semso_contributor)

	# Get groups from Semso Contributor
	employee_groups = []

	for row in semso_contributor or []:
		contribution = row.get("semso_contribution")

		if contribution:
			employee_groups.append(contribution)

	# Remove duplicate groups
	employee_groups = list(set(employee_groups))

	if not employee_groups:
		return []

	placeholders = ", ".join(["%s"] * len(employee_groups))

	# Amount is based on MAIN employee_group
	if employee_group == "Officer (RBA)":
		amount_field = "eg.officer_semso_amount"

	elif employee_group == "Troops (RBA)":
		amount_field = "eg.troop_semso_amount"

	elif employee_group == "Civilan (RBA)":
		amount_field = "eg.civilan_semso_amount"

	else:
		amount_field = "0"

	query = f"""
		SELECT
			e.name AS employee,
			e.employee_name as employee_name ,
			e.grade as grade,
			e.employee_group as employee_group,

			IFNULL({amount_field}, 0) AS amount

		FROM `tabEmployee` e

		INNER JOIN `tabEmployee Grade` eg
			ON e.grade = eg.name

		WHERE
			e.company = %s
			AND e.status = 'Active'
			AND e.employee_group IN ({placeholders})

		ORDER BY
			e.employee_group,
			e.employee_name
	"""

	values = [company] + employee_groups

	return frappe.db.sql(
		query,
		values,
		as_dict=True
	)

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator" or "System Manager" in user_roles or "HR User" in user_roles or "HR Manager" in user_roles: 
		return

	return """(
		exists(select 1
			from `tabEmployee` as e
			where e.branch = `tabSemso Entry`.branch
			and e.user_id = '{user}')
	)""".format(user=user)	