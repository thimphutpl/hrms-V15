# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cstr, cint, getdate, flt
from frappe import msgprint, _
from calendar import monthrange


def execute(filters=None):
	if not filters: filters = {}

	conditions, filters = get_conditions(filters)
	columns = get_columns(filters)
	att_map = get_attendance_list(conditions, filters)
	emp_map = get_employee_details(filters.employee_type)

	data = []
	
	count, total_mr, avg_mr = 0,0,0
	for key, values in att_map.items():
		# frappe.throw("<pre>{}</pre>".format(frappe.as_json(values)))
		count+=1
		month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov","Dec"][key-1]
		month_year='-'.join([month, filters.year])
		# frappe.throw(str(month_year))
		row = [f"<strong>{month_year}</strong>"] + [''] * 35
		data.append(row)
		for emp in sorted(values):
			emp_det = emp_map.get(emp)
			if not emp_det:
				continue

			row = [emp_det.person_name, emp_det.id_card, emp_det.nationality]

			total_p = total_a = 0.0
			# frappe.throw(str(monthrange(cint(filters.year), key)[1]))
			for day in range(31):
				# frappe.throw(str(values.get(emp).get(day + 1, "None")))
				status = values.get(emp).get(day + 1, "None")
				status_map = {"Present": "P", "Absent": "A", "Half Day": "H", "None": ""}
				row.append(status_map[status])
				# frappe.throw("<pre>{}</pre>".format(frappe.as_json(row)))
				if status == "Present":
					total_p += 1
				if status == "Half Day":
					total_p += flt(0.5, 2)
				elif status == "Absent":
					total_a += 1

			row += [total_p, total_a]
			data.append(row)
		total_emp = len(values)
		total_mr += flt(total_emp)
		row = [f"<b>Total</b>", total_emp] + [''] * 34
		data.append(row)
	
	if not filters.month:
		avg_mr = flt(total_mr/count)
		data.append([f"<b>Total number of MR for {filters.year}</b>",total_mr]+['']*34)
		data.append([f"<b>Average number of MR for {filters.year}</b>"+str(filters.year),avg_mr]+['']*34)
	# frappe.throw("<pre>{}</pre>".format(frappe.as_json(data)))

	return columns, data

def get_columns(filters):
	columns = [
		_("Name") + "::140", 
		_("CID")+ "::120",
		_("Nationality")+ "::100"
	]

	for day in range(31):
		columns.append(cstr(day+1) +"::45")

	columns += [_("Total Present") + "::100", _("Total Absent") + "::100"]
	return columns

def get_attendance_list(conditions, filters):
	attendance_list = frappe.db.sql("""select mr_employee as employee, day(date) as day_of_month, month(date) as month, year(date) as year,
		status from `tabMuster Roll Attendance` where docstatus = 1 %s order by month, mr_employee, date""" %
		conditions, filters, as_dict=1)

	att_map = {}
	for d in attendance_list:
		att_map.setdefault(d.month, frappe._dict()).setdefault(d.employee, frappe._dict()).setdefault(d.day_of_month, "")
		# att_map.setdefault(d.employee, frappe._dict()).setdefault(d.day_of_month, "")
		att_map[d.month][d.employee][d.day_of_month] = d.status
	# frappe.throw("<pre>{}</pre>".format(frappe.as_json(att_map)))
	
	return att_map

def get_conditions(filters):
	conditions = ''
	if not filters.get("year"):
		msgprint(_("Please select month and year"), raise_exception=1)

	# filters["total_days_in_month"] = 31 #monthrange(cint(filters.year), filters.month)[1]

	if filters.get('month'):
		filters["month"] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
		"Dec"].index(filters.month) + 1
		conditions = " and month(date) = %(month)s"
	conditions += " and year(date) = %(year)s and cost_center = \'" + str(filters.cost_center) + "\' "

	return conditions, filters

def get_employee_details(employee_type):
	emp_map = frappe._dict()
	if employee_type == "Muster Roll Employee":
		for d in frappe.db.sql("""select name, person_name, id_card, IFNULL(nationality,"")
			from `tabMuster Roll Employee`""", as_dict=1):
			emp_map.setdefault(d.name, d)

	return emp_map

@frappe.whitelist()
def get_years():
	year_list = frappe.db.sql_list("""select distinct YEAR(date) from `tabMuster Roll Attendance` ORDER BY YEAR(date) DESC""")
	if not year_list:
		year_list = [getdate().year]

	return "\n".join(str(year) for year in year_list)