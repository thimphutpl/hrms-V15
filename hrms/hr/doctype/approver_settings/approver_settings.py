# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document



class ApproverSettings(Document):
	pass

def get_final_approver(branch):
	if not branch:
		frappe.throw("Branch not passed")

	# Ver 3.0.190131 Begins, following code added by SHIV
	# For head office divisions, final approvers are set on child cost centers
	approver = frappe.db.get_value("Approver Settings", {"cost_center": get_branch_cc(branch)}, "user_id")

	if approver:
		return approver
	# Ver 3.0.190131 Ends

	cc = frappe.db.get_value("Cost Center", get_branch_cc(branch), "parent_cost_center")
	approver = frappe.db.get_value("Approver Settings", {"cost_center": cc}, "user_id")
	if not approver:
		frappe.throw("Setup the final approver in Approval Settings")
	return approver

def get_branch_cc(branch):
	if not branch:
		frappe.throw("No Branch Argument Found")
	doc = frappe.get_doc("Branch", branch)
	return doc.cost_center
