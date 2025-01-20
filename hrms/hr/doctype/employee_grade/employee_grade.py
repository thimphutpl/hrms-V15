# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.naming import set_name_by_naming_series, make_autoname
from frappe.utils import add_years, cint, get_link_to_form, getdate
from frappe.model.document import Document


class EmployeeGrade(Document):
	pass

# @frappe.whitelist()
# def get_retirement_date(date_of_birth=None):
# 	if date_of_birth:
# 		try:
# 			# retirement_age = cint(frappe.db.get_single_value("HR Settings", "retirement_age") or 60)
# 			retirement_age = (frappe.db.get_single_value("Employee Grade", "retirement_age") or 60)
# 			dt = add_years(getdate(date_of_birth), retirement_age)
# 			return dt.strftime("%Y-%m-%d")
# 		except ValueError:
# 			# invalid date
# 			return
