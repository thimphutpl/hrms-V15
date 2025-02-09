# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.utils import (
	add_days,
	ceil,
	cint,
	cstr,
	date_diff,
	floor,
	flt,
	formatdate,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	money_in_words,
	rounded,
)

class TravelClaim(Document):
	def validate(self):
		pass
		# self.calculate_amount()

	def calculate_amount(self):
		for d in self.get("items"):
			no_days   = date_diff(d.to_date, d.from_date) + 1
			d.amount = flt(no_days) * flt(dsa)

@frappe.whitelist()
def get_travel_claim(dt, dn):
	doc = frappe.get_doc(dt, dn)

	employee_grade = frappe.db.get_value("Employee", doc.employee, "grade")
	dsa = frappe.db.get_value("Employee Grade", employee_grade, "dsa")
	if not dsa:
		frappe.throw(
			"Daily Subsistence Allowance (DSA) is not set for Employee Grade: {}. Please update it.".format(
				frappe.get_desk_link("Employee Grade", employee_grade)
			),
			title="Missing DSA Configuration"
		)

	return_day_dsa = frappe.db.get_single_value("HR Settings", "return_day_dsa")

	tc = frappe.new_doc("Travel Claim")
	tc.posting_date = frappe.utils.nowdate()
	tc.employee = doc.employee
	tc.employee_name = doc.employee_name
	tc.travel_type = doc.travel_type
	tc.purpose_of_travel = doc.purpose_of_travel
	tc.mode_of_travel = doc.mode_of_travel
	tc.branch = doc.branch
	tc.cost_center = doc.cost_center

	for d in doc.get("items"):
		item = d.as_dict()
		if d.is_last_day == 1:
			item["dsa_percent"] = return_day_dsa if return_day_dsa else 100
			item["dsa"] = flt(dsa) * flt(item["dsa_percent"])/100
		else:
			item["dsa_percent"] = 100
			item["dsa"] = dsa
		item["no_of_days"] = date_diff(d.to_date, d.from_date) + 1
		item["amount"] = flt(item["no_of_days"]) * flt(item["dsa"])
		tc.append("items", item)

	tc.travel_authorization = doc.name
	tc.currency = doc.currency
	tc.exchange_rate = doc.exchange_rate

	return tc.as_dict()
