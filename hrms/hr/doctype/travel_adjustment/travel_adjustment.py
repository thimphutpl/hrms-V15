# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TravelAdjustment(Document):
	def validate(self):
		self.validate_travel_authorization()

	def on_submit(self):
		self.update_travel_authorization()
		self.update_authorizaiton_end_date()

	def on_cancel(self):
		self.update_travel_authorization(cancel=True)
		self.update_authorizaiton_end_date(cancel=True)

	def validate_travel_authorization(self):
		pass

	def update_travel_authorization(self, cancel=False):
		frappe.db.sql(
			"DELETE FROM `tabTravel Authorization Item` WHERE parent = %s", 
			(self.travel_authorization,)
		)
		if cancel:
			pass
		else:
			for item in self.new_travel_item:
				frappe.get_doc({
					"doctype": "Travel Authorization Item",
					"parenttype": "Travel Authorization",
					"parentfield": "items",
					"idx": item.idx,
					"parent": self.travel_authorization,
					"date": item.date,
					"to_date": item.to_date,
					"halt": item.halt,
					"halt_at": item.halt_at,
					"no_days": item.no_days,
					"travel_from": item.travel_from,
					"travel_to": item.travel_to,
				}).insert(ignore_permissions=True)

	def update_authorizaiton_end_date(self, cancel=False):
		doc = frappe.get_doc("Travel AUthorization", self.travel_authorization)
		if cancel:
			pass
		else:
			if self.items:
				doc.end_date_auth = self.items[len(self.items) - 1].from_date

