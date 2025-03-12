# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.utils import getdate


class MusterRollTransfer(Document):
	def validate(self):
		pass

	@frappe.whitelist()
	def fill_employee_details(self):
		self.set("items", [])
		filters = frappe._dict(
			company=self.company,
			branch=self.branch
		)
		employees = get_muster_roll_employee_list(filters)

		for emp in employees:
			self.append("items", emp)

	def before_submit(self):
		if getdate(self.posting_date) > getdate():
			frappe.throw(
				_("Employee Transfer cannot be submitted before Transfer Date"),
				frappe.DocstatusTransitionError,
			)
	
	def on_submit(self):
		self.validate_target_branch()
		self.update_muster_roll_employee_master()

	def validate_target_branch(self):
		if not self.get("items"):
			frappe.throw("The Items table cannot be empty. Please add at least one entry.")
		
		for d in self.get("items"):
			if not d.to_branch:
				frappe.throw(f"Please set Target Branch at Row {frappe.bold(d.idx)}")

	def on_cancel(self):
		for d in self.items:
			employee = frappe.get_doc("Muster Roll Employee", d.employee)

			last_work_entry = frappe.get_value(
				"Muster Roll Internal Work History",
				{"parent": employee.name, "reference_name": self.name},
				["branch", "from_date"],
			)

			update_mr_employee_work_history(employee, self.name, date=self.posting_date, cancel=True)

			if last_work_entry:
				employee.branch = last_work_entry[0]
				employee.date_of_joining = last_work_entry[1]

			employee.save()


	def update_muster_roll_employee_master(self):
		for d in self.get("items"):
			employee = frappe.get_doc("Muster Roll Employee", d.employee)

			employee = update_mr_employee_work_history(employee, self.name, date=self.posting_date)

			employee.branch = d.to_branch
			employee.date_of_joining = self.posting_date
			employee.save()

def update_mr_employee_work_history(employee, ref_name, date=None, cancel=False):
    if len(employee.internal_work_history) == 0 and not cancel:
        employee.append(
            "internal_work_history",
            {
                "reference_name": ref_name,
                "branch": employee.branch,
                "from_date": employee.date_of_joining,
                "to_date": date,
            },
        )

    if cancel:
        delete_mr_employee_work_history(employee, ref_name)

    return employee

def delete_mr_employee_work_history(employee, ref_name):
    frappe.db.delete("Muster Roll Internal Work History", {'parent': employee.name, 'reference_name': ref_name})
    frappe.db.commit()


def get_muster_roll_employee_list(filters: frappe._dict):
    Employee = frappe.qb.DocType("Muster Roll Employee")

    query = (
        frappe.qb.from_(Employee)
        .select(
            Employee.name.as_("employee"),
            Employee.employee_name
        )
        .where(
            (Employee.status == "Active") 
			& (Employee.company == filters.company) 
			& (Employee.branch == filters.branch)
        )
    )

    return query.run(as_dict=True)
