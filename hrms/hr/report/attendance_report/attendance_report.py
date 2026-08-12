
# import calendar
# from datetime import timedelta

# import frappe
# from frappe import _
# from frappe.utils import getdate
# SHIFT_MAP = {
# 		"Counter Summer Shift": "CSM",
# 		"Counter Winter Shift": "CWM",

# 		"Wangchutaba Summer Morning Shift": "WSM",
# 		"Wangchutaba Summer Evening Shift": "WSE",
# 		"Wangchutaba Summer Night Shift": "WSN",

# 		"Wangchutaba Winter Morning Shift": "WWM",
# 		"Wangchutaba Winter Evening Shift": "WWE",
# 		"Wangchutaba Winter Night Shift": "WWN",
# 		"Wangchutaba Winter General Shift": "WWG",

# 		"Lingmethang Summer Morning Shift": "LSM",
# 		"Lingmethang Summer Evening Shift": "LSE",
# 		"Lingmethang Summer Night Shift": "LSN",
# 		"Lingmethang Summer General Shift": "LSG",

# 		"Lingmethang Winter Morning Shift": "LWM",
# 		"Lingmethang Winter Evening Shift": "LWE",
# 		"Lingmethang Winter Night Shift": "LWN",
# 		"Lingmethang Winter General Shift": "LWG",

# 		"Head Office General Summer Shift": "HOGS",
# 		"Head Office Summer Saturday Shift": "HOSS",
# 		"Head Office Winter General Shift": "HOWG",
# 		"Head Office Winter Saturday Shift": "HWS",
# 		"general shift": "GEN"
# 	}

# def execute(filters=None):
# 	columns = get_columns(filters)
# 	data = get_data(filters)
# 	return columns, data


# def get_columns(filters):
# 	columns = [
# 		{
# 			"label": _("Employee"),
# 			"fieldname": "employee",
# 			"fieldtype": "Link",
# 			"options": "Employee",
# 			"width": 140,
# 		},
# 		{
# 			"label": _("Employee Name"),
# 			"fieldname": "employee_name",
# 			"fieldtype": "Data",
# 			"width": 180,
# 		},
# 	]

# 	from_date = getdate(filters.from_date)
# 	to_date = getdate(filters.to_date)

# 	current_date = from_date

# 	while current_date <= to_date:
# 		day_label = f"{current_date.day} {calendar.day_abbr[current_date.weekday()]}"
# 		columns.append(
# 			{
# 				"label": _(day_label),
# 				"fieldname": current_date.strftime("%Y_%m_%d"),
# 				"fieldtype": "Data",
# 				"width": 90,
# 			}
# 		)

# 		current_date += timedelta(days=1)

# 	return columns


# def get_data(filters):
# 	from_date = getdate(filters.from_date)
# 	to_date = getdate(filters.to_date)

# 	employees = frappe.get_all(
# 		"Employee",
# 		filters={"status": "Active"},
# 		fields=["name", "employee_name", "holiday_list"],
# 		order_by="name"
# 	)

# 	if not employees:
# 		return []

# 	attendance_list = frappe.get_all(
# 		"Attendance",
# 		filters={
# 			"attendance_date": ["between", [from_date, to_date]],
# 			"docstatus": 1
# 		},
# 		fields=[
# 			"employee",
# 			"attendance_date",
# 			"status",
# 			"shift"
# 		]
# 	)

# 	attendance_map = {}

# 	for att in attendance_list:
# 		key = (att.employee, str(att.attendance_date))
# 		attendance_map[key] = att

# 	data = []

# 	for emp in employees:
# 		row = {
# 			"employee": emp.name,
# 			"employee_name": emp.employee_name,
# 		}

# 		holidays = get_holidays(emp.holiday_list)

# 		current_date = from_date

# 		while current_date <= to_date:
# 			fieldname = current_date.strftime("%Y_%m_%d")

# 			key = (emp.name, str(current_date))

# 			value = "A"

# 			if get_holiday_status(current_date, holidays):
# 				value = "H"

# 			# Attendance Exists
# 			if key in attendance_map:
# 				att = attendance_map[key]

# 				# Present → Show Shift
# 				if att.status == "Present":
# 					# value = att.shift if att.shift else "P"
# 					value = SHIFT_MAP.get(att.shift, "P")

# 				# Leave
# 				elif att.status == "On Leave":
# 					value = "L"

# 				elif att.status == "Half Day":
# 					value = "HD"

# 				elif att.status == "Tour":
# 					value = "Tour"

# 				elif att.status == "Absent":
# 					value = "A"

# 			row[fieldname] = value

# 			current_date += timedelta(days=1)

# 		data.append(row)

# 	return data


# def get_holidays(holiday_list):
# 	if not holiday_list:
# 		return []

# 	holidays = frappe.get_all(
# 		"Holiday",
# 		filters={"parent": holiday_list},
# 		fields=["holiday_date"]
# 	)

# 	return [str(d.holiday_date) for d in holidays]


# def get_holiday_status(day, holidays):
# 	return str(day) in holidays

import calendar
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import getdate


# -----------------------------
# SHIFT SHORT CODE MAP
# -----------------------------
SHIFT_MAP = {
	"Counter Summer Shift": "CSM",
	"Counter Winter Shift": "CWM",

	"Wangchutaba Summer Morning Shift": "WSM",
	"Wangchutaba Summer Evening Shift": "WSE",
	"Wangchutaba Summer Night Shift": "WSN",
	"Wangchutaba Summer General Shift": "WSGN",

	"Wangchutaba Winter Morning Shift": "WWM",
	"Wangchutaba Winter Evening Shift": "WWE",
	"Wangchutaba Winter Night Shift": "WWN",
	"Wangchutaba Winter General Shift": "WWG",

	"Lingmethang Summer Morning Shift": "LSM",
	"Lingmethang Summer Evening Shift": "LSE",
	"Lingmethang Summer Night Shift": "LSN",
	"Lingmethang Summer General Shift": "LSG",

	"Lingmethang Winter Morning Shift": "LWM",
	"Lingmethang Winter Evening Shift": "LWE",
	"Lingmethang Winter Night Shift": "LWN",
	"Lingmethang Winter General Shift": "LWG",

	"Head Office General Summer Shift": "HOGS",
	"Head Office Summer Saturday Shift": "HOSS",
	"Head Office Winter General Shift": "HOWG",
	"Head Office Winter Saturday Shift": "HWS",

	"general shift": "GEN"
}


# -----------------------------
# EXECUTE
# -----------------------------
def execute(filters=None):
	if not filters:
		return [], []

	from_date = getdate(filters.from_date)
	to_date = getdate(filters.to_date)

	columns = get_columns(from_date, to_date)
	data = get_data(from_date, to_date)
	message = get_message()

	return columns, data,message


# -----------------------------
# COLUMNS
# -----------------------------
def get_columns(from_date, to_date):
	columns = [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 180,
		},
	]

	current = from_date
	while current <= to_date:
		columns.append({
			"label": f"{current.day} {calendar.day_abbr[current.weekday()]}",
			"fieldname": current.strftime("%Y_%m_%d"),
			"fieldtype": "Data",
			"width": 80,
		})
		current += timedelta(days=1)

	return columns


# -----------------------------
# DATA
# -----------------------------
def get_data(from_date, to_date):

	employees = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name", "holiday_list"],
		order_by="name"
	)

	attendance_list = frappe.get_all(
		"Attendance",
		filters={
			"attendance_date": ["between", [from_date, to_date]],
			"docstatus": 1
		},
		fields=["employee", "attendance_date", "status", "shift"]
	)

	# -----------------------------
	# ATTENDANCE MAP
	# -----------------------------
	attendance_map = {}
	for att in attendance_list:
		key = (att.employee, att.attendance_date.strftime("%Y-%m-%d"))
		attendance_map[key] = att

	data = []
	today = getdate()

	for emp in employees:
		row = {
			"employee": emp.name,
			"employee_name": emp.employee_name
		}

		holidays = get_holidays(emp.holiday_list)

		current = from_date
		
		while current <= to_date:

			field = current.strftime("%Y_%m_%d")
			date_key = current.strftime("%Y-%m-%d")
			key = (emp.name, date_key)

			# value = "A"

			if current > today:
				value = ""     # future date
			else:
				value = "A"    # absent default


			# -----------------------------
			# HOLIDAY
			# -----------------------------
			if is_holiday(date_key, holidays):
				value = "H"

			# -----------------------------
			# ATTENDANCE
			# -----------------------------
			if key in attendance_map:
				att = attendance_map[key]

				if att.status == "Present":
					value = get_shift_code(att.shift)
				elif att.status == "On Leave":
					value = "L"
				elif att.status == "Half Day":
					value = "HD"
				elif att.status == "Tour":
					value = "T"
				elif att.status == "Absent":
					value = "A"

			row[field] = value
			current += timedelta(days=1)

		data.append(row)

	return data


# -----------------------------
# SHIFT SHORT CODE FUNCTION
# -----------------------------
def get_shift_code(shift_name):
	if not shift_name:
		return "A" 
	return SHIFT_MAP.get(shift_name, "A")


def get_message() -> str:
	message = ""

	for status, abbr in SHIFT_MAP.items():
		message += f"""
			<li style="
				margin-bottom:6px;
				font-weight:500;
			">
				{status} → <b>{abbr}</b>
			</li>
		"""

	return f"""
		<ul style="
			padding-left:18px;
			list-style-type: disc;
		">{message}</ul>
	"""
# -----------------------------
def get_holidays(holiday_list):
	if not holiday_list:
		return []

	holidays = frappe.get_all(
		"Holiday",
		filters={"parent": holiday_list},
		fields=["holiday_date"]
	)

	return [d.holiday_date.strftime("%Y-%m-%d") for d in holidays]


def is_holiday(day, holidays):
	return day in holidays
