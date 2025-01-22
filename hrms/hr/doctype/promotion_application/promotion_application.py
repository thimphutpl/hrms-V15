# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class PromotionApplication(Document):
	
	def validate(self):
		pass

	def on_submit(self):
		# pass
		# Check if the employee is a supervisor
		emp_doc = frappe.get_doc("Employee", self.employee)
		if not emp_doc.reports_to:
			frappe.throw(("This employee is not a supervisor and cannot forward the promotion application."))

		supervisor_role = frappe.get_value("Employee", emp_doc.reports_to, "user_id")
		if frappe.session.user != supervisor_role:
			frappe.throw(("Only the supervisor can forward the promotion application."))


	
	@frappe.whitelist()
	def get_promotion_detail(self):
		#last_day of promotion
		last_date=frappe.db.sql("select promotion_date from `tabEmployee Promotion` where employee = '{}' order by promotion_date desc limit 1".format(self.employee), as_dict=True)
		emp_doc = frappe.get_doc("Employee", self.employee)

		# self.supervisor=frappe.get_value("Employee",emp_doc.reports_to, "user_id")
		self.supervisor=frappe.get_value("Employee",emp_doc.reports_to, "user_id")
		if not emp_doc.division:
			frappe.throw("Please assign division to the employee")
		self.hod=frappe.get_value("Department", emp_doc.division, "approver_hod")
		self.hod_user = frappe.get_value("Department", emp_doc.division, "approver_id")
		if last_date:
			self.last_date_of_promotion=last_date

		if len(self.edu_qualification)==0:
			for child in emp_doc.get_all_children():
				if child.doctype=="Employee Education":
					edu_child = frappe.get_doc("Employee Education", child.name)
					# frappe.throw(str(edu_child.course_name))
					self.append("edu_qualification",{
						"school_univ": edu_child.school_univ,
						"level": edu_child.level,
						"course_name": edu_child.course_name,
						"trade": edu_child.trade,
						"year_of_passing": edu_child.year_of_passing,
						"country": edu_child.country,
						"class_per": edu_child.class_per,
						"maj_opt_subj": edu_child.maj_opt_subj
					})

		eol_leaves=frappe.db.sql("select from_date, to_date, leaves from `tabLeave Ledger Entry` where leave_type='EOL' and employee='{}'".format(self.employee), as_dict=True)
		if len(eol_leaves)!=0:
			if len(self.eol_leaves):
				for row in eol_leaves:
					self.append("eol_leaves",
					{
						"duration": -1*flt(row.leaves),
						"from": row.from_date,
						"to": row.to_date
					})
			

		pms_rating = frappe.db.sql("select pms_calendar,final_score from `tabPerformance Evaluation` where employee='{}'".format(self.employee), as_dict=True)
		if len(pms_rating)!=0:
			if len(self.pms_rating) == 0:
				for row in pms_rating:
					self.append("pms_rating",
					{
						"fiscal_year": row.pms_calendar,
						"rating": row.final_score,
					})


@frappe.whitelist()
def validate_action(self, action):
	current_user = frappe.session.user

	if action in ["Forward", "Reject"] and self.employee == current_user:
		frappe.throw(("You are not allowed to {0} your own promotion application. Only your supervisor can perform this action.").format(action))




