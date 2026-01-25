# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, getdate, today
from datetime import datetime, timedelta
from frappe import _
from hrms.hr.utils import (
	get_distance_between_coordinates,
	set_geolocation_from_coordinates,
	validate_active_employee,
)
class EmployeeAttendance(Document):
	def validate(self):
		self.validate_ip_address()
		# self.validate_time_not_past()
		self.validate_duplicate_logs()
		self.validate_late()
		self.set_geolocation()
	def before_save(self):
		if not hasattr(self, "time") or not self.time:
			frappe.throw("Check-in / Check-out time (time) is required.")
		# Attendance date derived from check-in/out time
		self.attendance_date = getdate(self.time)

	# def after_insert(self):
	# 	if self.log_type == "OUT":
	# 		try:
	# 			self.create_attendance_from_checkins()
	# 		except Exception:
	# 			frappe.log_error(frappe.get_traceback(), f"Failed to create attendance for {self.employee}")
	def validate_ip_address(self):
		if not self.shift:
			return

		request_ip = (
			frappe.get_request_header("X-Forwarded-For")
			or frappe.local.request_ip
		)
		# frappe.throw(str(request_ip))

		allowed_ip = frappe.db.get_value(
			"Shift Type",
			self.shift,
			"ip"
		)
		if not allowed_ip:
			return

		allowed_ips = [ip.strip() for ip in allowed_ip.split(",")]
		if request_ip not in allowed_ips:
			frappe.throw(
				_(
					"Check-In / Check-Out is allowed only from office network.\n"
				)
			)
			
	def validate_time_not_past(self):
		"""Prevent check-ins/check-outs for past dates"""
		if get_datetime(self.time) < get_datetime(today()):
			frappe.throw(_("You cannot create check-in/check-out for past dates."))
	def validate_duplicate_logs(self):
		"""Prevent multiple IN or OUT logs for the same day"""
		if not self.time or not self.employee or not self.log_type:
			return

		start_of_day = datetime.combine(getdate(self.time), datetime.min.time())
		end_of_day = datetime.combine(getdate(self.time), datetime.max.time())

		existing_log = frappe.get_all(
			"Employee Attendance",
			filters={
				"employee": self.employee,
				"log_type": self.log_type,
				"time": ["between", [start_of_day, end_of_day]],
				"name": ("!=", self.name),
			},
			limit=1
		)

		if existing_log:
			frappe.throw(_(
				"You have already checked {0} for today.".format("in" if self.log_type=="IN" else "out")
			))
				
	def validate_late(self):
		if not self.time:
			return

		checkin_time = get_datetime(self.time)
		shift_start = self.get_real_shift_start()
		shift_end = self.get_real_shift_end()


		# -----------------------------
		# Late Entry (IN logs)
		# -----------------------------
		if self.log_type == "IN" and shift_start:
			grace_minutes = frappe.db.get_value("Attendance Shift", self.shift, "late_entry_grace_period") or 0
			grace_seconds = int(grace_minutes) * 60
			diff_seconds = (checkin_time - shift_start).total_seconds()
			if diff_seconds > grace_seconds:
				self.late_entry = 1
				self.late_hours = round(diff_seconds / 3600, 2)  # Calculate late hours
				if not getattr(self, "late_reason", None):
					frappe.throw(_("You are late. Please enter the reason for late check-in."))
			else:
				self.late_hours = 0

	# -----------------------------
	# Early Exit (OUT logs)
	# -----------------------------
		# if self.log_type == "OUT" and shift_end:
		# 	early_grace_minutes = frappe.db.get_value("Attendance Shift", self.shift, "early_exit_grace_period") or 0
		# 	early_grace_seconds = int(early_grace_minutes) * 60
		# 	diff_seconds = (shift_end - checkin_time).total_seconds()
		# 	if diff_seconds > early_grace_seconds:
		# 		self.early_exit = 1
		# 		self.early_exit_hours = round(diff_seconds / 3600, 2)  # Calculate early exit hours
		# 		if not getattr(self, "early_exit_reason", None):
		# 			frappe.throw(_("You are leaving early. Please enter the reason for early exit."))
		# 	else:
		# 		self.early_exit_hours = 0
		if self.log_type == "OUT" and shift_end:


			early_grace_minutes = frappe.db.get_value("Attendance Shift", self.shift, "early_exit_grace_period") or 0
			early_grace_seconds = int(early_grace_minutes) * 60

			# Use max to avoid negative early exit hours
			diff_seconds = (shift_end - checkin_time).total_seconds() - early_grace_seconds

			if diff_seconds > 0:  # Only mark early exit if OUT is before shift_end - grace
				self.early_exit = 1
				self.early_exit_hours = round(diff_seconds / 3600, 2)
				if not getattr(self, "early_exit_reason", None):
					frappe.throw(_("You are leaving early. Please enter the reason for early exit."))
			else:
				self.early_exit = 0
				self.early_exit_hours = 0
		# if self.log_type == "IN" and shift_start:
		# 	grace_minutes = frappe.db.get_value("Attendance Shift", self.shift, "late_entry_grace_period") or 0
		# 	grace_seconds = int(grace_minutes) * 60
		# 	diff_seconds = (checkin_time - shift_start).total_seconds()
		# 	if diff_seconds > grace_seconds:
		# 		self.late_entry = 1
		# 		if not getattr(self, "late_reason", None):
		# 			frappe.throw(_("You are late. Please enter the reason for late check-in."))

		# # -----------------------------
		# # Early Exit (OUT logs)
		# # -----------------------------
		# if self.log_type == "OUT" and shift_end:
		# 	early_grace_minutes = frappe.db.get_value("Attendance Shift", self.shift, "early_exit_grace_period")
		# 	early_grace_seconds = int(early_grace_minutes) * 60
		# 	diff_seconds = (shift_end - checkin_time).total_seconds()
		# 	if diff_seconds > early_grace_seconds:
		# 		self.early_exit = 1
		# 		if not getattr(self, "early_exit_reason", None):
		# 			frappe.throw(_("You are leaving early. Please enter the reason for early exit."))
			

	def create_attendance_from_checkins(self):
		# Get all IN/OUT logs for the employee today
		checkins = frappe.get_all(
			"Employee Attendance",
			filters={
				"employee": self.employee,
				"name": ("!=", self.name),
				# "time": ["between", [get_datetime(today()), get_datetime(today()) + timedelta(hours=23, minutes=59, seconds=59)]],
				"log_type": ["in", ["IN", "OUT"]],
			},
			fields=["name", "log_type", "time", "late_reason", "early_exit_reason"],
			order_by="time asc"
		)

		# Include current log
		checkins.append({
			"name": self.name,
			"log_type": self.log_type,
			"time": self.time,
			"late_reason": getattr(self, "late_reason", ""),
			"early_exit_reason": getattr(self, "early_exit_reason", "")
		})

		in_times = [get_datetime(c["time"]) for c in checkins if c["log_type"] == "IN"]
		out_times = [get_datetime(c["time"]) for c in checkins if c["log_type"] == "OUT"]

		if not in_times or not out_times:
			return

		first_in = min(in_times)
		last_out = max(out_times)

		# Get shift details
		shift_data = frappe.get_cached_value(
			"Attendance Shift", self.shift,
			["start_time", "end_time", "working_hours_threshold_for_half_day", "working_hours_threshold_for_absent"]
		)
		if not shift_data:
			frappe.throw(f"Shiftbnv {self.shift} not found")

		shift_start, shift_end, half_day_threshold, absent_threshold = shift_data
		shift_start = self._to_datetime(shift_start, first_in)
		shift_end = self._to_datetime(shift_end, last_out)
		if shift_end <= shift_start:
			shift_end += timedelta(days=1)
			

		# Calculate working hours within shift
		shift_work_start = max(first_in, shift_start)
		shift_work_end = min(last_out, shift_end)
		worked_hours = round((shift_work_end - shift_work_start).total_seconds() / 3600, 2)

		# Morning extra hours (before shift start)
		morning_extra_hours = round(max(0, (shift_start - first_in).total_seconds()) / 3600, 2)
		# Overtime (after shift end)
		overtime_hours = round(max(0, (last_out - shift_end).total_seconds()) / 3600, 2)

		# Determine attendance status
		if worked_hours >= half_day_threshold:
			attendance_status = "Present"
		elif absent_threshold <= worked_hours < half_day_threshold:
			attendance_status = "Half Day"
		else:
			attendance_status = "Absent"

		# Late / Early flags
		late_entry = first_in > shift_start
		early_exit = last_out < shift_end

		# Savepoint for safe insert
		frappe.db.savepoint("attendance_creation")

		# Create Attendance
		attendance = frappe.new_doc("Attendance")
		attendance.update({
			"employee": self.employee,
			"attendance_date": getdate(first_in),
			"status": attendance_status,
			"working_hours": worked_hours,
			"shift": self.shift,
			"late_entry": late_entry,
			"late_hours": round(max(0, (first_in - shift_start).total_seconds() / 3600), 2),
			"early_exit": early_exit,
			"early_exit_hours": round(max(0, (shift_end - last_out).total_seconds() / 3600), 2),
			"morning_extra_hours": morning_extra_hours,
			"overtime_hours": overtime_hours,
			"in_time": first_in,
			"out_time": last_out,
			"late_reason": next((c["late_reason"] for c in checkins if c["log_type"]=="IN" and c.get("late_reason")), ""),
			"early_exit_reason": next((c["early_exit_reason"] for c in checkins if c["log_type"]=="OUT" and c.get("early_exit_reason")), "")
		})
		attendance.insert(ignore_permissions=True)
		attendance.submit()
		log_names = [c["name"] for c in checkins]
		self.save(ignore_permissions=True)
		
		self.update_attendance_in_checkins(log_names, attendance.name)
		self.reload()
		return attendance
	def update_attendance_in_checkins(self, log_names: list, attendance_id: str):
		EmployeeCheckin = frappe.qb.DocType("Employee Attendance")
		(
			frappe.qb.update(EmployeeCheckin)
			.set("attendance", attendance_id)
			.where(EmployeeCheckin.name.isin(log_names))
		).run()
		



	@frappe.whitelist()
	def set_geolocation(self):
		set_geolocation_from_coordinates(self)	

	def _to_datetime(self, value, reference):
		if isinstance(value, str):
			return datetime.combine(getdate(reference), datetime.strptime(value, "%H:%M:%S").time())
		elif isinstance(value, datetime):
			return value
		elif isinstance(value, timedelta):
			return datetime.combine(getdate(reference), datetime.min.time()) + value
		else:
			frappe.throw(f"Unsupported shift time format: {value}")
	# def get_real_shift_start(self):
	# 	start_time = frappe.db.get_value("Attendance Shift", self.shift, "start_time")
	# 	if start_time:
	# 		return self._to_datetime(start_time, get_datetime(self.time))
	# 	return None

	# def get_real_shift_end(self):
	# 	end_time = frappe.db.get_value("Attendance Shift", self.shift, "end_time")
	# 	shift_start = self.get_real_shift_start()
	# 	if end_time and shift_start:
	# 		shift_end = self._to_datetime(end_time, get_datetime(self.time))
	# 		if shift_end <= shift_start:  
	# 			shift_end += timedelta()
	# 		return shift_end
	# 	return None
	def get_real_shift_start(self):
		shift_data = self._get_employee_shift()
		if shift_data:
			return self._to_datetime(shift_data['start_time'], get_datetime(self.time))
		return None

	def get_real_shift_end(self):
		shift_data = self._get_employee_shift()
		if shift_data:
			shift_end = self._to_datetime(shift_data['end_time'], get_datetime(self.time))
			shift_start = self._to_datetime(shift_data['start_time'], get_datetime(self.time))
			if shift_end <= shift_start:
				shift_end += timedelta(days=1)
			return shift_end
		return None

	def _get_employee_shift(self):
		"""Fetch the active shift for this employee today."""
		emp_branch = frappe.db.get_value("Employee", self.employee, "attendance_branch")
		shift = frappe.get_all(
			"Attendance Shift",
			filters={
				"name": self.shift,
				"attendance_branch": emp_branch,
				"is_active": 1,
				"valid_from": ["<=", getdate(self.time)],
				"valid_to": [">=", getdate(self.time)]
			},
			fields=["start_time", "end_time"],
			limit=1
		)
		if shift:
			return shift[0]
		frappe.throw(f"Could not find active shift '{self.shift}' for employee {self.employee} on {getdate(self.time)}")

def mark_absent_daily(attendance_date=None):
	"""
	Mark absent for employees who did not check-in/out and have no leave.
	This function can be triggered by scheduler daily.
	"""
	if not attendance_date:
		attendance_date = getdate(today())

	start_of_day = datetime.combine(attendance_date, datetime.min.time())
	end_of_day = datetime.combine(attendance_date, datetime.max.time())

	# Get all active employees
	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "attendance_branch"]
	)

	absent_count = 0

	for emp in employees:
		if not emp.attendance_branch:
			continue  # Skip if employee has no attendance branch

		# Get active shift for this branch today
		shift = frappe.get_all(
			"Attendance Shift",
			filters={
				"attendance_branch": emp.attendance_branch,
				"is_active": 1,
				"valid_from": ["<=", attendance_date],
				"valid_to": [">=", attendance_date],
			},
			fields=["name", "start_time", "end_time"],
			order_by="valid_from desc",
			limit=1
		)

		if not shift:
			continue  # Skip if no shift assigned

		shift_name = shift[0].name

		# Check if employee already has attendance for today
		checkins = frappe.get_all(
			"Employee Attendance",
			filters={
				"employee": emp.name,
				"time": ["between", [start_of_day, end_of_day]]
			},
			fields=["name"]
		)

		# Check if employee is on leave today
		leave_or_lr = frappe.get_all(
			"Leave Application",
			filters={
				"employee": emp.name,
				"from_date": ["<=", attendance_date],
				"to_date": [">=", attendance_date],
				"status": "Approved"
			},
			fields=["name"]
		)

		# If no check-ins/out and no leave, mark absent
		if not checkins and not leave_or_lr:
			attendance = frappe.new_doc("Attendance")
			attendance.update({
				"employee": emp.name,
				"attendance_date": attendance_date,
				"status": "Absent",
				"working_hours": 0,
				"shift": shift_name,
				"late_entry": 0,
				"late_hours": 0,
				"early_exit": 0,
				"early_exit_hours": 0,
				"in_time": None,
				"out_time": None,
				"morning_extra_hours": 0,
				"overtime_hours": 0,
			})
			attendance.insert(ignore_permissions=True)
			attendance.submit()
			absent_count += 1

	frappe.log_error(f"Absent Attendance marked for {absent_count} employees on {attendance_date}", "Attendance Scheduler")
	return absent_count


# Scheduler wrapper
def daily_absent_scheduler():
	return mark_absent_daily()
def schedule_auto_attendance(doc, method):
	if doc.log_type == "OUT":
		doc.create_attendance_from_checkins()
	  