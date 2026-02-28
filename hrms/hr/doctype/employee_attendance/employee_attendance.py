# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import get_datetime, getdate, today, nowdate
from datetime import datetime, timedelta,time
from frappe import _
from hrms.hr.utils import (
	get_distance_between_coordinates,
	set_geolocation_from_coordinates,
	validate_active_employee,
)
class EmployeeAttendance(Document):
	def validate(self):
		self.validate_ip_address()
		self.validate_time_not_past()
		self.validate_duplicate_logs()
		self.validate_late()
		self.set_geolocation()

	
	def before_save(self):
		if not hasattr(self, "time") or not self.time:
			frappe.throw("Check-in / Check-out time (time) is required.")
		# Attendance date derived from check-in/out time
		self.attendance_date = getdate(self.time)

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
	
	def create_attendance_from_checkins(self):


		first_in = frappe.db.get_value(
			"Employee Attendance",
			{"employee":self.employee, "log_type": "IN"},
			"time",
			order_by="creation desc"
		)
		last_out =get_datetime(self.time)

		checkins = frappe.get_all(
			"Employee Attendance",
			filters={
				"employee": self.employee,
				"name": ("!=", self.name),
				"time": ["between", [first_in, last_out]],
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

		shift_work_start = max(first_in, shift_start)
		shift_work_end = min(last_out, shift_end)
		worked_hours = round((shift_work_end - shift_work_start).total_seconds() / 3600, 2)

		morning_extra_hours = round(max(0, (shift_start - first_in).total_seconds()) / 3600, 2)
		overtime_hours = round(max(0, (last_out - shift_end).total_seconds()) / 3600, 2)

		if worked_hours >= half_day_threshold:
			attendance_status = "Present"
		elif absent_threshold <= worked_hours < half_day_threshold:
			attendance_status = "Half Day"
		else:
			attendance_status = "Absent"

		late_entry = first_in > shift_start
		early_exit = last_out < shift_end

		frappe.db.savepoint("attendance_creation")

	
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
	def get_real_shift_start(self):
		start_time = frappe.db.get_value("Attendance Shift", self.shift, "start_time")
		if start_time:
			return self._to_datetime(start_time, get_datetime(self.time))
		return None

	def get_real_shift_end(self):
		end_time = frappe.db.get_value("Attendance Shift", self.shift, "end_time")
		shift_start = self.get_real_shift_start()
		if end_time and shift_start:
			shift_end = self._to_datetime(end_time, get_datetime(self.time))
			if shift_end <= shift_start:  
				shift_end += timedelta()
			return shift_end
		return None
	
def schedule_auto_attendance(doc, method):
	if doc.log_type == "OUT":
		doc.create_attendance_from_checkins()


def auto_mark_absent():
    today = getdate(nowdate())
    weekday_name = today.strftime("%A")  # "Monday", "Tuesday", etc.

    # Get all active employees
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "company", "attendance_branch"]
    )

    for emp in employees:

        if not emp.attendance_branch:
            continue

        # Get all active shifts for this employee's branch
        shifts = frappe.get_all(
            "Attendance Shift",
            filters={
                "attendance_branch": emp.attendance_branch,
                "is_active": 1,
            },
            fields=["name"]
        )

        shift_for_today = None
        for s in shifts:
            doc = frappe.get_doc("Attendance Shift", s.name)

            # Check valid_from / valid_to
            if doc.valid_from and today < doc.valid_from:
                continue
            if doc.valid_to and today > doc.valid_to:
                continue

            # Check if today is a working day
            working_days = [d.day for d in doc.week]  # list of strings like ["Monday", "Tuesday"]
            if weekday_name not in working_days:
                continue

            # Check holiday
            if doc.holiday_list and frappe.db.exists("Holiday", {
                "parent": doc.holiday_list,
                "holiday_date": today
            }):
                continue

            # Found the shift that applies today
            shift_for_today = doc
            break

        if not shift_for_today:
            frappe.log_error(f"No shift applies today for branch {emp.attendance_branch}", "Auto Mark Absent")
            continue

        shift = shift_for_today

        # Skip if attendance already exists
        if frappe.db.exists("Attendance", {
            "employee": emp.name,
            "attendance_date": today
        }):
            continue

        # Skip if approved leave exists
        if frappe.db.exists("Leave Application", {
            "employee": emp.name,
            "from_date": ["<=", today],
            "to_date": [">=", today],
            "status": "Approved"
        }):
            continue

        # Skip if Employee Checkin logs exist today
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)

        has_log = frappe.db.exists("Employee Attendance", {
            "employee": emp.name,
            "time": ["between", [start, end]]
        })

        if has_log:
            continue

        # Create Absent Attendance
        attendance = frappe.get_doc({
            "doctype": "Attendance",
            "employee": emp.name,
            "attendance_date": today,
            "status": "Absent",
            "company": emp.company,
            "shift": shift.name,
            "remark": "Marked Absent due to missing check-in and check-out."
        })
        attendance.insert(ignore_permissions=True)
        attendance.submit()

    frappe.db.commit()