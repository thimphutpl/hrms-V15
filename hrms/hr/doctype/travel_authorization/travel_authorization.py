# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from hrms.hr.utils import validate_active_employee
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
	nowdate
)
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states

class TravelAuthorization(Document):
	def validate(self):

		validate_active_employee(self.employee)
		
		self.validate_travel_dates()
		self.validate_travel_last_day()
		self.validate_exchange_rate()
		self.set_status()
		self.make_travel_advance()
		self.validate_estimated_amount()
		validate_workflow_states(self)

	def on_update(self):
		self.check_date_overlap()
		self.validate_duplicate_entry()

	def on_submit(self):
		if self.advance_amount: 
			self.post_journal_entry()

	def on_cancel(self):
		self.set_status(update=True)

	def set_status(self, update=False):
		status_map = {0: "Draft", 1: "Submitted", 2: "Cancelled"}
		status = status_map.get(self.docstatus, "Unknown")

		if update:
			self.db_set("status", status)
		else:
			self.status = status

	def validate_estimated_amount(self):
		if flt(self.advance_amount) > flt(self.estimated_amount):
			frappe.throw("Your estimate amount is less than advance amount ")
		if flt(self.advance_amount) > (flt(self.estimated_amount) * 0.75):
			frappe.throw("Your estimate amount cannot be more than 75% of the estimated amount")

	def post_journal_entry(self):
		advance_account = frappe.db.get_value("Company", self.company, "travel_advance_account")
		bank_account = frappe.db.get_value("Branch", self.branch, "expense_bank_account")
		#frappe.throw(advance_account)

		if not advance_account:
			frappe.throw(
				"Travel Advance Account is not set for {}. Please configure it in the Company.".format(
					frappe.get_desk_link("Company", self.company)
				),
				title="Missing Travel Advance Account"
			)

		if not bank_account:
			frappe.throw(
				"Default Expense Bank Account is not set for {}. Please configure it in the Branch.".format(
					frappe.get_desk_link("Branch", self.branch)
				),
				title="Missing Expense Bank Account"
			)

		# Posting Journal Entry
		accounts = []
		accounts.append({
			"account": advance_account,
			"debit": flt(self.advance_amount),
			"debit_in_account_currency": flt(self.advance_amount),
			"cost_center": self.cost_center,
			"party_check": 1,
			"party_type": "Employee",
			"party": self.employee,
			"is_advance": "Yes",
			"reference_type": "Travel Authorization",
			"reference_name": self.name,
		})

		accounts.append({
			"account": bank_account,
			"credit": flt(self.advance_amount),
			"credit_in_account_currency": flt(self.advance_amount),
			"cost_center": self.cost_center,
		})

		je = frappe.new_doc("Journal Entry")
		
		voucher_type = "Bank Entry"
		naming_series = "Bank Payment Voucher"
		
		je.update({
				"doctype": "Journal Entry",
				"voucher_type": voucher_type,
				"naming_series": naming_series,
				"title": "Travel Advance - "+self.employee,
				"user_remark": "Travek Advance - "+self.employee,
				"posting_date": nowdate(),
				"company": self.company,
				"accounts": accounts,
				"branch": self.branch
		})

		if self.advance_amount:
			je.save(ignore_permissions = True)
			self.db_set("journal_entry", je.name)
			# self.db_set("journal_entry_status", "Forwarded to accounts for processing payment on {0}".format(now_datetime().strftime('%Y-%m-%d %H:%M:%S')))
			# frappe.msgprint(_('{} posted to accounts').format(frappe.get_desk_link(je.doctype,je.name)))

	def validate_travel_dates(self):
		for item in self.get("items", []):
			if cint(item.halt):
				self._validate_halt_entry(item)
			else:
				self._validate_travel_entry(item)

	def _validate_halt_entry(self, item):
		if not item.halt_at:
			frappe.throw(
				_("Row#{}: <b>Halt at</b> is mandatory.").format(item.idx),
				title="Missing Halt Information"
			)
		if not item.to_date:
			frappe.throw(
				_("Row#{0}: <b>Till Date</b> is mandatory.").format(item.idx),
				title="Invalid Date"
			)
		if item.to_date < item.from_date:
			frappe.throw(
				_("Row#{0}: <b>Till Date</b> cannot be earlier than <b>From Date</b>.").format(item.idx),
				title="Invalid Date"
			)

	def _validate_travel_entry(self, item):
		if not (item.travel_from and item.travel_to):
			frappe.throw(
				_("Row#{0}: <b>Travel From</b> and <b>Travel To</b> are mandatory.").format(item.idx),
				title="Missing Travel Information"
			)
		item.to_date = item.from_date  # Ensuring `to_date` is set for non-halt cases

	def check_date_overlap(self):
		overlap_query = """
			SELECT t1.idx, t2.idx AS overlap_idx
			FROM `tabTravel Authorization Item` t1
			JOIN `tabTravel Authorization Item` t2
			ON t1.parent = t2.parent
			AND t1.name != t2.name
			AND t1.from_date <= t2.to_date
			AND t1.to_date >= t2.from_date
			WHERE t1.parent = %s
		"""

		overlaps = frappe.db.sql(overlap_query, (self.name,), as_dict=True)
		if overlaps:
			first_overlap = overlaps[0]
			frappe.throw(
				_("Row#{}: Dates are overlapping with dates in Row#{}").format(
					first_overlap["idx"], first_overlap["overlap_idx"]
				),
				title="Date Overlap Detected"
			)

	def validate_duplicate_entry(self):
		duplicate_query = """
			SELECT 
				t3.idx, 
				t1.name AS authorization_name, 
				t2.from_date, 
				t2.to_date 
			FROM `tabTravel Authorization` t1
			JOIN `tabTravel Authorization Item` t2 ON t2.parent = t1.name
			JOIN `tabTravel Authorization Item` t3 ON t3.parent = %s
			WHERE 
				t1.employee = %s
				AND t1.docstatus != 2
				AND t1.workflow_state != 'Rejected'
				AND t1.name != %s
				AND t2.from_date <= t3.to_date
				AND t2.to_date >= t3.from_date
		"""

		overlaps = frappe.db.sql(duplicate_query, (self.name, self.employee, self.name), as_dict=True)

		if overlaps:
			t = overlaps[0]
			frappe.throw(
				_("Row #{}: This request overlaps with {} ({} to {}).").format(
					t.idx, 
					frappe.get_desk_link("Travel Authorization", t.authorization_name), 
					t.from_date, 
					t.to_date
				),
				title=_("Duplicate Travel Entry")
			)

	def validate_travel_last_day(self):
		items = self.get("items", [])
		if len(items) > 1:
			for item in items:
				item.is_last_day = 0
			items[-1].is_last_day = 1

	def validate_exchange_rate(self):
		if not self.exchange_rate and self.travel_type != 'Domestic':
			frappe.throw(_("Exchange Rate cannot be zero."), title="Missing Exchange Rate")

	@frappe.whitelist()
	def has_travel_claim(self) -> dict[str, bool]:
		ta = frappe.qb.DocType("Travel Claim")

		travel_claim = (
			frappe.qb.from_(ta)
			.select(ta.name)
			.where(
				(ta.docstatus < 2)
				& (ta.travel_authorization == self.name)
			)
		).run(as_dict=True)

		return {
			"has_travel_claim": bool(travel_claim)
		}
	@frappe.whitelist()
	def make_travel_advance(self):
		"""
		Creates a Travel Advance document linked to the given Travel Authorization.
		"""
		no_of_days_in = 0
		no_of_days_out = 0
		
		
		for d in self.items:
			if d.is_last_day == 1:
				no_of_day = 0
			else:
				no_of_day = date_diff(d.to_date, d.from_date) + 1
				
				if d.country == 'Bhutan':
					no_of_days_in += no_of_day
				else:
					no_of_days_out += no_of_day
		
		
		employee_grade = frappe.db.get_value("Employee", self.employee, "grade")
		return_day_dsa = frappe.db.get_single_value("HR Settings", "return_day_dsa")
		
		
		base_dsa = frappe.db.get_value("Employee Grade", employee_grade, "dsa")
		
		#frappe.throw(str(base_dsa))
		dsa_in = base_dsa * no_of_days_in
		
		
		dsa_out = 0
		
		
		if self.travel_type == "International":
			for ds in self.items:
				if ds.country != "Bhutan" and ds.country:
					
					country_doc = frappe.get_doc("DSA Out Country", ds.country)
					if not country_doc:
						frappe.throw(f"DSA not set for country: {ds.country} in DSA Out Country")
					
				
					grade_found = False
					for dsa_detail in country_doc.country_dsa_detail:
						if dsa_detail.grade == employee_grade:
							
							daily_dsa_out = dsa_detail.dsa * self.exchange_rate
							
							
							if ds.is_last_day == 1:
								country_days = 0
							else:
								country_days = date_diff(ds.to_date, ds.from_date) + 1
							
							dsa_out += daily_dsa_out * country_days
							grade_found = True
							break
					
					if not grade_found:
						frappe.throw(f"DSA not set for grade {employee_grade} in country {ds.country}")
		else:
			
			dsa_out = base_dsa * no_of_days_out
		
		
		return_day_amount = (flt(return_day_dsa) / 100 * flt(base_dsa))
		
		
		self.estimated_amount = flt(dsa_in) + flt(dsa_out) + flt(return_day_amount)


		
		
		
@frappe.whitelist()
def get_approver(employee):
	# leave_approver, department = frappe.db.get_value("Employee", employee, ["leave_approver", "department"])

	# if not leave_approver and department:
	# 	leave_approver = frappe.db.get_value(
	# 		"Department Approver",
	# 		{"parent": department, "parentfield": "leave_approvers", "idx": 1},
	# 		"approver",
	# 	)
	department = frappe.db.get_value("Employee", employee, "department")
	empid=frappe.db.get_value("Department", department, "approver")
	approver = frappe.db.get_value("Employee", empid, "user_id")


	return approver


@frappe.whitelist()
def get_reports_to(employee):
	empid = frappe.db.get_value("Employee", employee, "reports_to")
	reports_to = frappe.db.get_value("Employee", empid, "user_id")
	
	return reports_to
def get_permission_query_conditions(user):
	
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)
	if "HR User" in user_roles or "HR Manager" in user_roles or "Accounts User" in user_roles or "CEO" in user_roles:
		
		return
	
	else:
		
		return """(
			name in (select name
				from `tabTravel Authorization`
				where  owner='{user}' or verifier='{user}' or approver = '{user}')
		)""".format(user=user)

def has_record_permission(doc, user):
	return True

	
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if "HR User" in user_roles or "HR Manager" in user_roles:
		return True
	else:			
		if frappe.db.exists("Employee", {"name":doc.name, "user_id": user}):
			return True
		else:
			return False