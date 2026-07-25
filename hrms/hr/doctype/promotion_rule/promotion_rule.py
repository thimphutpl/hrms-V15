# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PromotionRule(Document):
	def validate(self):
		self.generate_pay_scale()
	def generate_pay_scale(self):
		self.pay_scale = []

		basic = self.lower_limit
		level = 1

		while basic <= self.upper_limit:
			self.append("pay_scale", {
				"level": level,
				"amount": basic
			})

			basic += self.increment
			level += 1
		if self.pay_scale and self.pay_scale[-1].amount != self.upper_limit:
			self.append("pay_scale", {
				"level": level,
				"amount": self.upper_limit
			})