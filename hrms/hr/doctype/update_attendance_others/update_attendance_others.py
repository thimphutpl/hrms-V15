# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UpdateAttendanceOthers(Document):
	def validate(self):
		self.check_attendance()

	def on_submit(self):
		self.update_attendance()

	def on_cancel(self):
		self.update_attendance()

	def check_attendance(self):
		for row in self.get("items"):
			if row.employee_type != self.employee_type:
				if self.employee_type in("DFG","GFG") and row.employee_type=="DFG AND GFG":
					if not row.emp_cat:
						frappe.throw("Employee Category is required when employee type is DFG AND GFG")
					else:
						attendance = frappe.db.get_value("Attendance Others",{"date":row.date, "employee_type":row.employee_type,"cost_center":self.cost_center,"emp_cat":row.emp_cat},"name")
				else:
					frappe.throw("Please Select Same Employee Type")
			else:
				attendance = frappe.db.get_value("Attendance Others",{"date":row.date, "employee_type":row.employee_type,"cost_center":self.cost_center},"name")
			if not attendance:
				frappe.throw("Attendance record not found")

			attendance_doc = frappe.get_doc("Attendance Others", attendance)
			row.attendance_others_reference = attendance_doc.name
			row.current_attendance = attendance_doc.status

	def update_attendance(self):
		for row in self.get("items"):
			if row.current_attendance == row.attendance:
				frappe.throw("There is nothing to Update when Current Attendance is same as Update Attendance at raw {idx}".format(idx=row.idx))
			elif self.docstatus == 1:
				frappe.db.sql("""update `tabAttendance Others` set status='{attendance}' where name='{name}'""".format(attendance=row.attendance, name=row.attendance_others_reference)) 
			elif self.docstatus == 2:
				frappe.db.sql("""update `tabAttendance Others` set status='{attendance}' where name='{name}'""".format(attendance=row.current_attendance, name=row.attendance_others_reference)) 
			else:
				frappe.throw("couldn't submit or cancel")