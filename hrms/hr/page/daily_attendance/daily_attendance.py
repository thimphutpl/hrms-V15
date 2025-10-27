import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, date_diff, nowdate,now_datetime,format_time
from frappe.utils.data import get_first_day, get_last_day, add_days
from erpnext.custom_utils import get_year_start_date, get_year_end_date
from erpnext.setup.doctype.employee.employee import get_holiday_list_for_employee
import json
import logging
from datetime import datetime, timedelta
import datetime
import calendar

@frappe.whitelist()
def sign_in():
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    
    if not employee:
        frappe.throw("No employee found for the current user.")
    
    today = getdate()
    
    # Check if attendance already exists for today
    existing_attendance = frappe.db.exists("Daily Attendance Entry", {
        "employee": employee,
        "attendance_date": today,
        "docstatus": ["<", 2]  # Draft or Submitted
    })
    
    existing_leave = frappe.db.exists("Leave Application", {
        "employee": employee,
        "from_date": ("<=", today),
        "to_date":(">=", today)
        "docstatus": 1  # Draft or Submitted
    })

    # existing_holiday = frappe.db.exists("Daily Attendance Entry", {
    #     "employee": employee,
    #     "attendance_date": today,
    #     "docstatus": ["<", 2]  # Draft or Submitted
    # })
    if existing_attendance:
        frappe.throw("Attendance for today already exists.")
    
    # Create new attendance record
    attendance = frappe.new_doc("Daily Attendance Entry")
    attendance.employee = employee
    attendance.attendance_date = today
    attendance.status = "Half Day"  # Initial status
    attendance.sign_in_time = now_datetime()
    attendance.flags.ignore_permissions = True
    attendance.insert()
    
    return {"message": "Sign-in successful", "attendance": attendance.name}

@frappe.whitelist()
def sign_out():
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    
    if not employee:
        frappe.throw("No employee found for the current user.")
    
    today = getdate()
    
    # Get the attendance record for today
    existing_attendance = frappe.db.exists("Daily Attendance Entry", {
        "employee": employee,
        "attendance_date": today,
        "docstatus": ["<", 2],
        "status":"Present"
    })
    attendance_name = frappe.db.get_value("Daily Attendance Entry", {
        "employee": employee,
        "attendance_date": today,
        "docstatus": 0  # Draft document
    }, "name")
    
    if not attendance_name:
        frappe.throw("No sign-in found for today.")
    
    if existing_attendance:
        frappe.throw("You have alread sign out")

    attendance = frappe.get_doc("Daily Attendance Entry", attendance_name)
    attendance.sign_out_time = now_datetime()
    attendance.status = "Present"  # Update status to Present
    attendance.flags.ignore_permissions = True
    attendance.save()
    
    return {"message": "Sign-out successful", "attendance": attendance.name}


@frappe.whitelist()
def get_todays_attendance():
    employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")
    today = nowdate()
    
    attendance = frappe.get_value("Daily Attendance Entry", {
        "employee": employee,
        "attendance_date": today
        
    }, ["sign_in_time", "sign_out_time"], as_dict=True)
    
    if attendance:
        return {
            "sign_in_time": format_time(attendance.sign_in_time) if attendance.sign_in_time else "",
            "sign_out_time": format_time(attendance.sign_out_time) if attendance.sign_out_time else ""
        }
    
    return {}

@frappe.whitelist()
def is_ip_authorized(ip_address):
    
    office_ip = frappe.db.get_single_value("HR Settings", "office_gobal_ip")
    return  office_ip==ip_address
    
    # if ip_address in allowed_ips:
    #     return True
    
    # return False




@frappe.whitelist()
def get_holidays(employee, from_date, to_date, holiday_list=None):
	"""get holidays between two dates for the given employee"""
	if not holiday_list:
		holiday_list = get_holiday_list_for_employee(employee)

	holidays = frappe.db.sql(
		"""select count(distinct holiday_date) from `tabHoliday` h1, `tabHoliday List` h2
		where h1.parent = h2.name and h1.holiday_date between %s and %s
		and h2.name = %s""",
		(from_date, to_date, holiday_list),
	)[0][0]

	return holidays