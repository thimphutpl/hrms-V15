# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.naming import set_name_by_naming_series, make_autoname
from frappe.utils import add_years, cint, get_link_to_form, getdate
from frappe.model.document import Document


class EmployeeGrade(Document):
	pass

