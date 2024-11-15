from collections.abc import Generator

import requests

import frappe
from frappe.utils import add_days, date_diff

country_info = {}


@frappe.whitelist(allow_guest=True)
def get_country(fields=None):
	global country_info
	ip = frappe.local.request_ip

	if ip not in country_info:
		fields = ["countryCode", "country", "regionName", "city"]
		res = requests.get(
			"https://pro.ip-api.com/json/{ip}?key={key}&fields={fields}".format(
				ip=ip, key=frappe.conf.get("ip-api-key"), fields=",".join(fields)
			)
		)

		try:
			country_info[ip] = res.json()

		except Exception:
			country_info[ip] = {}

	return country_info[ip]


def get_date_range(start_date: str, end_date: str) -> list[str]:
	"""returns list of dates between start and end dates"""
	no_of_days = date_diff(end_date, start_date) + 1
	return [add_days(start_date, i) for i in range(no_of_days)]


def generate_date_range(start_date: str, end_date: str, reverse: bool = False) -> Generator[str, None, None]:
	no_of_days = date_diff(end_date, start_date) + 1

	date_field = end_date if reverse else start_date
	direction = -1 if reverse else 1

	for n in range(no_of_days):
		yield add_days(date_field, direction * n)


def get_employee_email(employee_id: str) -> str | None:
	employee_emails = frappe.db.get_value(
		"Employee",
		employee_id,
		["prefered_email", "user_id", "company_email", "personal_email"],
		as_dict=True,
	)

	return (
		employee_emails.prefered_email
		or employee_emails.user_id
		or employee_emails.company_email
		or employee_emails.personal_email
	)

def update_employee(employee, details, date=None, cancel=False):
	internal_work_history = {}
	new_pro_date = None
	for a in details:
		next_promotion_years = frappe.db.get_value("Employee Grade",a.new,"next_promotion_years")
		if next_promotion_years and next_promotion_years > 0:
			new_pro_date = add_years(date,int(frappe.db.get_value("Employee Grade",a.new,"next_promotion_years")))
	# details.extend(frappe._dict({'fieldname': 'promotion_due_date', 'new': new_pro_date, 'current': date}))
	setattr(employee, 'promotion_due_date', new_pro_date)
	internal_work_history['promotion_due_date'] = new_pro_date
	for item in details:
		fieldtype = frappe.get_meta("Employee").get_field(item.fieldname).fieldtype
		new_data = item.new if not cancel else item.current
		if fieldtype == "Date" and new_data:
			new_data = getdate(new_data)
		elif fieldtype =="Datetime" and new_data:
			new_data = get_datetime(new_data)
		setattr(employee, item.fieldname, new_data)
		if item.fieldname in ["department", "designation", "branch", "grade", "promotion_due_date"]:
			internal_work_history[item.fieldname] = item.new
			internal_work_history["reference_doctype"] = item.parenttype
			internal_work_history["reference_docname"] = item.parent
	if internal_work_history and not cancel:
		internal_work_history["from_date"] = date
		employee.append("internal_work_history", internal_work_history)
	return employee
