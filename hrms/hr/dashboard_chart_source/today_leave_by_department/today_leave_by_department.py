import frappe
from frappe.utils import today


@frappe.whitelist()
def get_data(chart_name=None, filters=None, from_date=None, to_date=None, time_interval=None, timespan=None):
	today_date = today()

	data = frappe.db.sql(
		"""
		select
			coalesce(emp.branch, 'No Branch') as branch,
			count(distinct la.employee) as leave_count
		from `tabLeave Application` la
		inner join `tabEmployee` emp
			on emp.name = la.employee
		where
			la.docstatus = 1
			and la.status = 'Approved'
			and la.from_date <= %(today_date)s
			and la.to_date >= %(today_date)s
		group by emp.branch
		order by leave_count desc
		""",
		{"today_date": today_date},
		as_dict=True,
	)

	return {
		"labels": [d.branch for d in data],
		"datasets": [
			{
				"name": "On Leave Today",
				"values": [d.leave_count for d in data],
			}
		]
	}