# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import datetime


class UpdateAttendanceOthers(Document):
	def validate(self):
		self.check_attendance()

	def on_submit(self):
		self.update_attendance()

	def on_cancel(self):
		self.update_attendance()

	def check_attendance(self):
		for row in self.get("items"):
			start_date = row.date
			end_date = getattr(row, 'to_date', None) or row.date
			if isinstance(start_date, str):
				start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
			if isinstance(end_date, str):
				end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
			current_date = start_date
			attendance_others_reference_map = {}
			current_attendance_map = {}
			while current_date <= end_date:
				if row.employee_type != self.employee_type:
					if self.employee_type in ("DFG", "GFG") and row.employee_type == "DFG AND GFG":
						if not row.emp_cat:
							frappe.throw("Employee Category is required when employee type is DFG AND GFG")
						else:
							attendance = frappe.db.get_value(
								"Attendance Others",
								{"date": current_date, "employee_type": row.employee_type, "cost_center": self.cost_center, "emp_cat": row.emp_cat, "employee": row.employee},
								"name"
							)
					else:
						frappe.throw("Please Select Same Employee Type")
				else:
					attendance = frappe.db.get_value(
						"Attendance Others",
						{"date": current_date, "employee_type": row.employee_type, "cost_center": self.cost_center, "employee": row.employee},
						"name"
					)
				if not attendance:
					frappe.throw(f"Attendance record not found for date {current_date}")

				attendance_others_reference_map[str(current_date)] = attendance
				attendance_doc = frappe.get_doc("Attendance Others", attendance)
				current_attendance_map[str(current_date)] = attendance_doc.status
				current_date += datetime.timedelta(days=1)
			# Optionally, store the last attendance reference/status in the row fields
			if attendance_others_reference_map:
				last_date = str(end_date)
				row.attendance_others_reference = attendance_others_reference_map[last_date]
				row.current_attendance = current_attendance_map[last_date]
			# Store the maps as local attributes (not saved to DB)
			row._attendance_others_reference_map = attendance_others_reference_map
			row._current_attendance_map = current_attendance_map

	def update_attendance(self):
		for row in self.get("items"):
			start_date = row.date
			end_date = getattr(row, 'to_date', None) or row.date
			if isinstance(start_date, str):
				start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
			if isinstance(end_date, str):
				end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
			current_date = start_date
			attendance_ref_map = getattr(row, '_attendance_others_reference_map', {})
			current_att_map = getattr(row, '_current_attendance_map', {})
			while current_date <= end_date:
				attendance_ref = attendance_ref_map.get(str(current_date))
				current_att = current_att_map.get(str(current_date))
				if current_att == row.attendance:
					frappe.throw(f"There is nothing to Update when Current Attendance is same as Update Attendance at row {row.idx} for date {current_date}")
				elif self.docstatus == 1:
					frappe.db.sql(
						"""update `tabAttendance Others` set status=%s where name=%s""",
						(row.attendance, attendance_ref)
					)
				elif self.docstatus == 2:
					frappe.db.sql(
						"""update `tabAttendance Others` set status=%s where name=%s""",
						(current_att, attendance_ref)
					)
				else:
					frappe.throw("couldn't submit or cancel")
				current_date += datetime.timedelta(days=1)