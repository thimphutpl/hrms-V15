# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = get_employees(filters)

	return columns, data


def get_columns():
	return [
		_("Employee") + ":Link/Employee:120",
		_("Name") + ":Data:200",
		_("Date of Birth") + ":Date:100",
		_("Branch") + ":Link/Branch:120",
		_("Department") + ":Link/Department:120",
		_("Designation") + ":Link/Designation:120",
		_("Status")+":Data:50",
		_("Blood Ground")+":Data:50",
		_("Gender") + "::60",
		_("School/University")+":Data:100",
		_("Qualification")+":Data:100",
		_("Level")+":Data:100",
		_("Year Of Passing")+":Data:100",
		_("Title")+":Data:100",
		_("Year")+":Data:100",
		_("Description")+":Data:100",
	]


def get_employees(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql(
		"""
		SELECT
			e.name,
			e.employee_name,
			e.date_of_birth,
			e.branch,
			e.department,
			e.status,
			e.designation,
			e.blood_group,
			e.gender,
			ed.school_univ,
			ed.qualification,
			ed.class_per,
			ed.year_of_passing,
			a.title,
			a.year,
			a.description
		FROM 
			tabEmployee e
		LEFT JOIN `tabEmployee Education` ed
			ON ed.parent = e.name AND ed.parenttype='Employee'
		LEFT JOIN `tabAward` a
			ON a.parent = e.name AND a.parenttype='Employee'
		WHERE e.status = 'Active' {conditions}
		""".format(conditions=conditions),
		filters,  
		as_list=1,
	)



def get_conditions(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " and company = '%s'" % filters["company"].replace("'", "\\'")
	if filters.get("employee"):
		conditions += "AND e.name = %(employee)s"
	if filters.get("blood_group"):
		conditions += "AND blood_group=%(blood_group)s"	

	return conditions
