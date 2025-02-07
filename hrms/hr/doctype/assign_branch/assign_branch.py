# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AssignBranch(Document):
	def validate(self):
		self.assign_name()	
		# self.check_mandatory()
		self.check_employee_duplicate()
		self.check_duplicate()


	def check_mandatory(self):
		if not self.user:
			frappe.throw("User Id is Mandatory")	

	def on_update(self):
		# self.assign_branch()
		pass
	
	def assign_name(self):
		if self.employee:
			emp = frappe.get_doc(self.employee_type, self.employee)
			self.user = emp.user_id
			self.company = emp.company
			self.current_branch = emp.branch
			self.employee_name = emp.employee_name
		else:
			frappe.throw("Employee ID is Mandatory")

	def check_employee_duplicate(self):
		docs = frappe.db.sql("select name from `tabAssign Branch` where employee = %s and user = %s and name != %s", (self.employee, self.user, self.name), as_dict=True)
		if docs:
			frappe.throw("The Employee has been already assigned Branch through <b>" + str(docs[0].name) + "</b>")

	def check_duplicate(self):		
		for a in self.items:
			for b in self.items:
				if a.branch == b.branch and a.idx != b.idx:
					frappe.throw("Duplicate Entries for Branch in row " + str(a.idx) + " and " + str(b.idx))
		for a in self.assign_project:
			for b in self.assign_project:
				if a.project == b.project and a.idx != b.idx:
					frappe.throw("Duplicate Entries for Project in row " + str(a.idx) + " and " + str(b.idx))

	def assign_branch(self):
		#Clear user branch permissions 
		user_perms = frappe.defaults.get_user_permissions(self.user)
		for doc, names in user_perms.items():
			if doc == 'Branch':
				for a in names:
					frappe.permissions.remove_user_permission(doc, a, self.user)
			
		#Add the branch permissions back as per assigned branches
		frappe.permissions.add_user_permission("Branch", self.current_branch, self.user)
		for a in self.items:
			frappe.permissions.add_user_permission('Branch', a.branch, self.user)

		frappe.msgprint("Branch Assigned")

	#Populate branches with active branches 
	@frappe.whitelist()
	def get_all_branches(self):
		query = "select name as branch from tabBranch where disabled != 1" 
		entries = frappe.db.sql(query, as_dict=True)
		self.set('items', [])

		for d in entries:
			row = self.append('items', {})
			row.update(d)
	@frappe.whitelist()
	def get_all_project(self):
		if not self.action:
			frappe.throw("Choose Action First")
		if not self.branch:
			if self.action =="Add":
				entries = frappe.db.sql("""select name as project 
					from `tabProject` 
					where project_engineer!='{}'
					""".format(self.employee),as_dict=True)
				self.set('assign_project', [])
				for d in entries:
					row = self.append('assign_project', {})
					row.update(d)
			else:
				self.set('assign_project', [])
		else:
			if self.action =="Add":
				entries = frappe.db.sql("""select name as project 
					from `tabProject` 
					where branch='{}'
					""".format(self.branch),as_dict=True)
				for d in entries:
					row = self.append('assign_project', {})
					row.update(d)
			else:
				self.set('assign_project', [])


