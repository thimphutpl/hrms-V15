import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, date_diff, nowdate
from frappe.utils.data import get_first_day, get_last_day, add_days
from erpnext.custom_utils import get_year_start_date, get_year_end_date
import json
import logging
from datetime import datetime, timedelta
import datetime
import calendar

@frappe.whitelist()
def get_payroll_settings(employee=None):
		settings = {}
		if employee:
			settings = frappe.db.sql("""
						select
							e.employee_group,
							e.grade,
							d.sws,
							d.gis,
							g.health_contribution,
							g.employee_pf,
							g.employer_pf
						from `tabEmployee` e, `tabEmployee Group` g, `tabEmployee Grade` d
						where e.name = '{}'
						and g.name = e.employee_group
						and d.name = e.grade
				""".format(employee), as_dict=True)
		settings = settings[0] if settings else frappe._dict()
		return settings

@frappe.whitelist()
def get_salary_tax(gross_amt):
	tax_amount = max_amount = 0
	max_limit = frappe.db.sql("""select max(b.to_amount)
		from `tabIncome Tax Slab` a, `tabTaxable Salary Slab` b
		where now() between a.effective_from and ifnull(a.effective_till, now())
		and b.parent = a.name
	""")
	if not (gross_amt or max_limit):
		return tax_amount
	max_amount = flt(max_limit[0][0])

	if flt(gross_amt) > flt(max_amount):
		tax_amount = ((flt(gross_amt) - 125000.00) * 0.30) + 20208.00
	else:
		result = frappe.db.sql("""select ifnull(b.tax,0) from
			`tabIncome Tax Slab` a, `tabTaxable Salary Slab` b
			where now() between a.effective_from and ifnull(a.effective_till, now())
			and b.parent = a.name
			and %s between ifnull(b.from_amount,0) and ifnull(b.to_amount,0)
			limit 1
			""", flt(gross_amt))

		if result:
			tax_amount = result[0][0]

	return flt(tax_amount)

@frappe.whitelist()
def get_month_details(year, month):
	ysd = frappe.db.get_value("Fiscal Year", year, "year_start_date")
	if ysd:
		from dateutil.relativedelta import relativedelta
		import calendar, datetime
		diff_mnt = cint(month)-cint(ysd.month)
		if diff_mnt<0:
			diff_mnt = 12-int(ysd.month)+cint(month)
		msd = ysd + relativedelta(months=diff_mnt) # month start date
		month_days = cint(calendar.monthrange(cint(msd.year) ,cint(month))[1]) # days in month
		med = datetime.date(msd.year, cint(month), month_days) # month end date
		return frappe._dict({
			'year': msd.year,
			'month_start_date': msd,
			'month_end_date': med,
			'month_days': month_days
		})
	else:
		frappe.throw(_("Fiscal Year {0} not found").format(year))