# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EndUserTraining(Document):
	pass

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles or "GM" in user_roles:
		return

	return """(
		`tabEnd User Training`.owner = '{user}'
		or
		exists(select 1
			from `tabEmployee`
			where `tabEmployee`.name = `tabEnd User Training`.employee
			and `tabEmployee`.user_id = '{user}' and `tabEnd User Training`.docstatus != 2)
		)""".format(user=user)