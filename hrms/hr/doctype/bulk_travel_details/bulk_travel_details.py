# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc


class BulkTravelDetails(Document):
	pass

@frappe.whitelist()
def make_bulk_travel_claim(source_name, target_doc=None):
	# def update_date(obj, target, source_parent):
	# 	company_currency = frappe.get_cached_value("Company", obj.company, "default_currency")
	# 	advance_amount = 0
	# 	if obj.currency != company_currency:
	# 		advance_amount = flt(obj.base_advance_amount)
	# 	else:
	# 		advance_amount = flt(obj.advance_amount)
		
	# 	target.posting_date = nowdate()
	# 	target.advance_amount = flt(advance_amount)
	# 	target.supervisor = None

	# def transfer_currency(obj, target, source_parent):
	# 	if obj.halt:
	# 		target.from_place = None
	# 		target.to_place = None
	# 	else:
	# 		target.no_days = 1
	# 		target.halt_at = None

	# 	for item in source_parent.items:
	# 		if source_parent.currency == "BTN":
	# 			target.dsa = item.dsa
	# 		else:
	# 			target.base_dsa = item.dsa

	# 	target.country=obj.country
		
	def adjust_last_date(source, target):
		return
		# dsa_percent = frappe.db.get_single_value("HR Settings", "return_day_dsa")
		# for d in target.items:
		# 	if d.is_last_day == 1:
		# 		d.total_dsa = flt(d.total_dsa) * flt(dsa_percent)/100

	doc = get_mapped_doc("Bulk Travel Details", source_name, {
			"Bulk Travel Details": {
				"doctype": "Bulk Travel Claim",
				"field_map": {
					"name": "bulk_travel_details",
					"posting_date": "ta_date",
				},
				# "postprocess": update_date,
				"validation": {"docstatus": ["=", 0]}
			},
			"Bulk Travel Details Item": {
				"doctype": "Bulk Travel Claim Item",
				# "postprocess": transfer_currency,
			},
		}, target_doc, adjust_last_date)
	return doc	
