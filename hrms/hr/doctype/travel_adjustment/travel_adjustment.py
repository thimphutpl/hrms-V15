# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import cint, date_diff
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class TravelAdjustment(Document):
	def validate(self):
		validate_workflow_states(self)
		self.validate_travel_dates(update=True)
		self.validate_travel_last_day()

	def on_submit(self):
		self.update_travel_authorization()
		self.update_authorizaiton_end_date()

	def on_cancel(self):
		self.update_travel_authorization(cancel=True)
		self.update_authorizaiton_end_date(cancel=True)

	def validate_travel_last_day(self):
		if len(self.get("items")) > 1:
			self.items[-2].is_last_day = 0
			self.items[-1].is_last_day = 1

	def validate_travel_dates(self, update=False):
		for item in self.get("items"):
			if cint(item.halt):
				if not item.halt_at:
					frappe.throw(_("Row#{}: <b>Halt at</b> is mandatory").format(item.idx))
				elif not item.to_date:
					frappe.throw(_("Row#{0}: <b>To Date</b> is mandatory").format(item.idx),title="Invalid Date")
				elif item.from_date and item.to_date and (item.to_date < item.from_date):	
					frappe.throw(_("Row#{0}: <b>To Date</b> cannot be earlier to <b>From Date</b>").format(item.idx),title="Invalid Date")
			else:
				if not (item.travel_from and item.travel_to):
					frappe.throw(_("Row#{0}: <b>Travel From</b> and <b>Travel To</b> are mandatory").format(item.idx))
				item.to_date = item.from_date
			from_date = item.from_date
			to_date   = item.from_date if not item.to_date else item.to_date
			item.no_days   = date_diff(to_date, from_date) + 1
			if update:
				frappe.db.set_value("Travel Adjustment Item", item.name, "no_days", item.no_days)
		if self.items:
			# check if the travel dates are already used in other travel authorization
			tas = frappe.db.sql("""select t3.idx, t1.name, t2.from_date, t2.to_date
					from 
						`tabTravel Authorization` t1, 
						`tabTravel Authorization Item` t2,
						`tabTravel Authorization Item` t3
					where t1.employee = "{employee}"
					and t1.docstatus != 2
					and t1.workflow_state !="Rejected"
					and t1.name != "{travel_authorization}"
					and t2.parent = t1.name
					and t3.parent = "{travel_authorization}"
					and (
						(t2.from_date <= t3.to_date and t2.to_date >= t3.from_date)
						or
						(t3.from_date <= t2.to_date and t3.to_date >= t2.from_date)
					)
			""".format(travel_authorization = self.name, employee = self.employee), as_dict=True)
			for t in tas:
				frappe.throw("Row#{}: The dates in your current Travel Authorization have already been claimed in {} between {} and {}"\
					.format(t.idx, frappe.get_desk_link("Travel Authorization", t.name), t.from_date, t.to_date))

	def update_travel_authorization(self, cancel=False):
		frappe.db.sql(
			"DELETE FROM `tabTravel Authorization Item` WHERE parent = %s", 
			(self.travel_authorization,)
		)
		if cancel:
			for item in self.travel_authorization_items:
				frappe.get_doc({
					"doctype": "Travel Authorization Item",
					"parenttype": "Travel Authorization",
					"parentfield": "items",
					"idx": item.idx,
					"parent": self.travel_authorization,
					"from_date": item.from_date,
					"to_date": item.to_date,
					"halt": item.halt,
					"halt_at": item.halt_at,
					"no_days": item.no_days,
					"travel_from": item.travel_from,
					"travel_to": item.travel_to,
					"is_last_day": item.is_last_day,
				}).insert(ignore_permissions=True)
		else:
			for item in self.items:
				frappe.get_doc({
					"doctype": "Travel Authorization Item",
					"parenttype": "Travel Authorization",
					"parentfield": "items",
					"idx": item.idx,
					"parent": self.travel_authorization,
					"from_date": item.from_date,
					"to_date": item.to_date,
					"halt": item.halt,
					"halt_at": item.halt_at,
					"no_days": item.no_days,
					"travel_from": item.travel_from,
					"travel_to": item.travel_to,
					"is_last_day": item.is_last_day,
				}).insert(ignore_permissions=True)

	def update_authorizaiton_end_date(self, cancel=False):
		doc = frappe.get_doc("Travel Authorization", self.travel_authorization)
		if cancel:
			# doc.end_date_auth = self.items[len(self.travel_authorization_items) - 1].from_date
			doc.db_set("end_date_auth", self.travel_authorization_items[len(self.travel_authorization_items) - 1].from_date)

			doc.db_set("travel_adjustment", "")

		else:
			if self.items:
				# doc.end_date_auth = self.items[len(self.items) - 1].from_date
				doc.db_set("end_date_auth", self.items[len(self.items) - 1].from_date)
				doc.db_set("travel_adjustment", self.name)
				# frappe.throw(str(doc.end_date_auth))
		# doc.save()
