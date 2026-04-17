import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = get_columns()
	data = get_data(filters)

	return columns, data


def get_columns():
	return [
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140,
		},
		{
			"label": _("Name"),
			"fieldname": "name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Activity Code"),
			"fieldname": "aactivity_code",
			"fieldtype": "Link",
			"options": "Budget Activity",
			"width": 180,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120,
		},
		{
			"label": _("Company"),
			"fieldname": "company",
			"fieldtype": "Link",
			"options": "Company",
			"width": 160,
		},
		{
			"label": _("Advance Amount"),
			"fieldname": "advance_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Opening Balance"),
			"fieldname": "opening_balance",
			"fieldtype": "Currency",
			"width": 180,
		},
		{
			"label": _("Total Outstanding"),
			"fieldname": "total_outstanding",
			"fieldtype": "Currency",
			"width": 180,
		},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("ea.company = %(company)s")
		values["company"] = filters.company

	if filters.get("employee"):
		conditions.append("ea.employee = %(employee)s")
		values["employee"] = filters.employee

	if filters.get("from_date"):
		conditions.append("ea.posting_date >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("to_date"):
		conditions.append("ea.posting_date <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("docstatus") is not None and str(filters.get("docstatus")) != "":
		conditions.append("ea.docstatus = %(docstatus)s")
		values["docstatus"] = int(filters.docstatus)

	where_clause = " AND ".join(conditions)
	if where_clause:
		where_clause = "WHERE " + where_clause

	data = frappe.db.sql(
		f"""
		SELECT
			ea.employee_name,
			ea.employee,
			ea.posting_date,
			ea.company,
			ea.advance_amount,
			ea.advance_account
		FROM `tabEmployee Advance` ea
		{where_clause}
		ORDER BY ea.posting_date DESC, ea.name DESC
		""",
		values,
		as_dict=True,
	)

	return data
