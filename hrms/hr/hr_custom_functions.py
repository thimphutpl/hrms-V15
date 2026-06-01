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

def post_leave_credits(today=None):
	"""
		:param today: First day of the month
		:param employee: Employee id for individual allocation
		
		This method allocates leaves in bulk as per the leave credits defined in Employee Group master.
		It is mainly used for allocating monthly and yearly leave credits automatically through hooks.py.
		However, it can also be used for allocating manually if in case the automatic allocation failed
		for some reason.

		To run manually: Just pass the first day of the month to this method as argument. Following example
				allocates monthly credits for the period from '2019-01-01' till '2019-01-31', and yearly
				credits for the period from '2019-01-01' till '2019-12-31' as defined in Employee Group
				master for all the leave types except `Earned Leave`. Monthly credits for `Earned Leave`
				are allocated for the previous month i.e from '2018-12-01' till '2018-12-31'.

				Example:
					# Executing from console
					bench execute erpnext.hr.hr_custom_functions.post_leave_credits --args "'2019-01-01',"
	"""

	# Logging
	logging.basicConfig(format='%(asctime)s|%(name)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
	logger = logging.getLogger(__name__)
	
	today      = getdate(today) if today else getdate(nowdate())
	start_date = ''
	end_date   = ''

	first_day_of_month = 1 if today.day == 1 else 0
	first_day_of_year  = 1 if today.day == 1 and today.month == 1 else 0
		
	# if first_day_of_month or first_day_of_year:
	f_date = get_first_day(add_days(today, -today.day))
	t_date   = get_last_day(f_date)
	elist = frappe.db.sql("""
		select
			t1.name, t1.employee_name, t1.date_of_joining,
			(
			case
				when day(t1.date_of_joining) > 1 and day(t1.date_of_joining) <= 15
				then timestampdiff(MONTH,t1.date_of_joining,'{0}')+1 
				else timestampdiff(MONTH,t1.date_of_joining,'{0}')       
			end
			) as no_of_months,
			t2.leave_type, t2.credits_per_month, t2.credits_per_year,
			t3.is_carry_forward
		from `tabEmployee` as t1, `tabEmployee Group Item` as t2, `tabLeave Type` as t3
		where t1.status = 'Active'
		and t1.date_of_joining <= '{0}'
		and t1.employee_group = t2.parent
		and (t2.credits_per_month > 0 or t2.credits_per_year > 0)
		and t3.name = t2.leave_type
		and not exists(select 1
					  from `tabLeave Allocation` as t4
					  where t4.employee = t1.name
					  and t4.docstatus != 2 
					  and t4.from_date = '{1}'
					  and t4.to_date = '{2}'
					  and t4.leave_type = t3.name
					  )
		order by t1.name, t2.leave_type
	""".format(str(today), f_date, t_date), as_dict=1)

	counter = 0
	for e in elist:
		counter += 1
		leave_allocation = []
		credits_per_month = 0
		credits_per_year = 0
		
		if flt(e.no_of_months) <= 0:
			logger.error("{0}|{1}|{2}|{3}|{4}".format("NOT QUALIFIED",counter,e.name,e.employee_name,e.leave_type))
			continue

		# Monthly credits
		# For Earned Leaved monthly credits are given for previous month
		if flt(e.credits_per_month) > 0 and e.leave_type == "Earned Leave":
			total_working_days = 0
			total_leaves = 0
			start_date = get_first_day(add_days(today, -20))
			end_date   = get_last_day(start_date)
			emplist = frappe.db.sql("""
			select a.employee, a.employee_name, a.from_date, a.to_date 
			from `tabLeave Application` a inner join `tabLeave Type` b on a.leave_type = b.name 
			inner join `tabLeave Type Item` c on b.name = c.parent 
			where (a.from_date between '{0}' and '{1}' or a.to_date 
			between '{0}' and '{1}' or '{2}' between a.from_date and a.to_date)
			and a.employee = '{3}'
			and c.leave_type = 'Earned Leave' 
			and a.docstatus = 1 
			union select employee, employee_name, from_date, to_date 
			from  `tabEmployee Disciplinary Record` 
			where (from_date between '{0}' and '{1}' or to_date between '{0}' and '{1}' 
			or '{2}' between from_date and to_date) and employee = '{3}' 
			and not_guilty_or_acquitted = 0 and docstatus = 1
			""".format(str(start_date), str(end_date), str(today), e.name), as_dict=1)					
			if emplist:
				total_days_in_month = date_diff(end_date, start_date)
				leave_allocation_per_day = flt(e.credits_per_month/total_days_in_month)
				for l in emplist:	
					#Incase of leave within the month
					if l.from_date >= start_date and l.to_date <= end_date:
						total_leaves = total_leaves + date_diff(l.to_date, l.from_date)
					#Incase of leave starting before the month and ending within the month(Not the last day of the month)
					elif l.from_date < start_date and l.to_date < end_date:
						total_leaves = total_leaves + date_diff(l.to_date, start_date)
					#Incase of leave starting within the month(Not first day of the month) and but ends in other months
					elif l.from_date > start_date and l.to_date > end_date:
						total_leaves = total_leaves + date_diff(end_date, l.from_date)
				total_working_days = total_days_in_month - total_leaves

				credits_per_month = flt(total_working_days) * flt(leave_allocation_per_day)
				logger.info("{0}|{1}|{2}|{3}|{4}|{5}".format(e.name,e.employee_name,e.leave_type,flt(total_working_days),flt(credits_per_month),flt(leave_allocation_per_day)))
				
			else:
				# For Earned Leaved monthly credits are given for previous month
				credits_per_month = flt(e.credits_per_month)

		else:
			start_date = get_first_day(today)
			end_date   = get_last_day(start_date)

		leave_allocation.append({
			'from_date': str(start_date),
			'to_date': str(end_date),
			'new_leaves_allocated': flt(credits_per_month)
		})

		# Yearly credits
		if flt(e.credits_per_year) > 0:
			start_date = get_year_start_date(today)
			end_date   = get_year_end_date(start_date)

			leave_allocation.append({
				'from_date': str(start_date),
				'to_date': str(end_date),
				'new_leaves_allocated': flt(e.credits_per_year)
			})

		for la in leave_allocation:
			if not frappe.db.exists("Leave Allocation", {"employee": e.name, "leave_type": e.leave_type, "from_date": la['from_date'], "to_date": la['to_date'], "docstatus": ("<",2)}):
				try:
					doc = frappe.new_doc("Leave Allocation")
					doc.employee             = e.name
					doc.employee_name        = e.employee_name
					doc.leave_type           = e.leave_type
					doc.from_date            = la['from_date']
					doc.to_date              = la['to_date']
					doc.carry_forward        = cint(e.is_carry_forward)
					doc.new_leaves_allocated = flt(la['new_leaves_allocated'])
					doc.submit()
					logger.info("{0}|{1}|{2}|{3}|{4}|{5}".format("SUCCESS",counter,e.name,e.employee_name,e.leave_type,flt(la['new_leaves_allocated'])))
				except Exception as ex:
					logger.exception("{0}|{1}|{2}|{3}|{4}|{5}".format("FAILED",counter,e.name,e.employee_name,e.leave_type,flt(la['new_leaves_allocated'])))
			else:
				logger.warning("{0}|{1}|{2}|{3}|{4}|{5}".format("ALREADY ALLOCATED",counter,e.name,e.employee_name,e.leave_type,flt(la['new_leaves_allocated'])))

	#else:
		#        logger.info("Date {0} is neither beginning of the month nor year".format(str(today)))
		#        return 0
		
def adjust_el():
	# Logging
	logging.basicConfig(format='%(asctime)s|%(name)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
	logger = logging.getLogger(__name__)
	
	####### To overwrite or adjust auto Earned Leave allocation when employee's leave falls within the month ######## 	
	emplist = frappe.db.sql("""
			   select employee, employee_name, from_date, to_date, total_leave_days
			   from `tabLeave Application` where 
			   (from_date between DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH,'%Y-%m-01') and LAST_DAY(CURDATE() - INTERVAL 1 Month)
			   or to_date between DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH,'%Y-%m-01') and LAST_DAY(CURDATE() - INTERVAL 1 Month))
			   and docstatus = 1
			   and exists (select 1
				   from `tabLeave Type` 
				   where dont_allocate_el = 1) 
			   order by employee 	
			   """, as_dict=1)
	
	cur_date = getdate(nowdate())
	first = datetime.date(day=1, month=cur_date.month, year=cur_date.year)

	#Previous Month End Date
	end_date = first - datetime.timedelta(days=1)
	print(end_date)
	#Previous Month Start Date
	start_date = datetime.date(day=1, month=end_date.month, year=end_date.year)
	print(start_date)

	#Get Total no of days in amonth
	total_days = calendar.monthrange(start_date.year, start_date.month)[1]

	for l in emplist:
		print(l.to_date)
		#Incase of leave within the month
		if l.from_date >= start_date and l.to_date <= end_date:
			no_of_leave_days = l.total_leave_days
			allocated_el = flt(0.08 * (total_days - no_of_leave_days))
		#Incase of leave starting before the month and ending within the month(Not the last day of the month)
		elif l.from_date < start_date and l.to_date < end_date:
			first_date = datetime.strptime(l.to_date, "%Y-%m-%d")
			second_date = datetime.strptime(start_date, "%Y-%m-%d")
			no_of_leave_days = (first_date - second_date).days
			allocated_el = flt(0.08 * (total_days - no_of_leave_days))				
		#Incase of leave starting within the month(Not first day of the month) and but ends in other months
		elif l.from_date > start_date and l.to_date > end_date:
			first_date = datetime.strptime(end_date, "%Y-%m-%d")
			second_date = datetime.strptime(l.from_date, "%Y-%m-%d")
			no_of_leave_days = (first_date - second_date).days
			allocated_el = flt(0.08 * (total_days - no_of_leave_days))
		is_carry_forward = frappe.get_value("Leave Type", "Earned Leave", "is_carry_forward")
		print("+++ ")
		#Checks whether EL has been allocated or not	
		if frappe.db.exists("Leave Allocation", {"employee": l.employee, "leave_type": "Earned Leave", "from_date": start_date, "to_date": end_date, "docstatus": ("<",2)}):
			doc = frappe.get_doc("Leave Allocation", {"employee": l.employee, "leave_type":"Earned Leave", "from_date": start_date, "to_date": end_date, "docstatus": ("<",2)})
			total_leaves = flt(doc.total_leaves_allocated) - flt(doc.new_leaves_allocated) + flt(allocated_el)
			doc.db_set("new_leaves_allocated", allocated_el)
			doc.db_set("total_leaves_allocated", total_leaves)
			logger.info("{0}|{1}|{2}|{3}|{4}".format("SUCCESS",l.name,l.employee_name,"Modified Existing allocation",flt(allocated_el)))
		else:
			doc = frappe.new_doc("Leave Allocation")
			doc.employee             = l.employee
			doc.employee_name        = l.employee_name
			doc.leave_type           = "Earned Leave"
			doc.from_date            = start_date
			doc.to_date              = end_date
			doc.carry_forward        = cint(is_carry_forward)
			doc.new_leaves_allocated = flt(allocated_el)
			doc.submit()
			logger.info("{0}|{1}|{2}|{3}|{4}".format("SUCCESS",l.name,l.employee_name,"Created new allocation", flt(allocated_el)))

# +++++++++++++++++++++ VER#2.0#CDCL#886 ENDS +++++++++++++++++++++

##
# Post casual leave on the first day of every month
##
def post_casual_leaves():
	date = getdate(frappe.utils.nowdate())
	if not (date.month == 1 and date.day == 1):
		return 0
	date = add_days(frappe.utils.nowdate(), 10)
	start = get_year_start_date(date);
	end = get_year_end_date(date);
	# employees = frappe.db.sql("select name, employee_name from `tabEmployee` where status = 'Active'", as_dict=True)
	employees = frappe.db.sql("""
		select name, employee_name
		from `tabEmployee`
		where status = 'Active'
		and employment_type not in ('GCE', 'Armed Forces')
	""", as_dict=True)

	for e in employees:
		la = frappe.new_doc("Leave Allocation")
		la.employee = e.name
		la.employee_name = e.employee_name
		la.leave_type = "Casual Leave"
		la.from_date = str(start)
		la.to_date = str(end)
		la.carry_forward = cint(0)
		la.new_leaves_allocated = flt(10)
		la.submit()


# start --Added By Karma
def post_earned_leaves():
	from hrms.hr.doctype.leave_application.leave_application import (
		get_leave_balance_on,
	)
	today = getdate(nowdate())
	if today != get_last_day(today):
		return 0 

	# Fiscal year = calendar year
	fiscal_start = today.replace(month=1, day=1)
	fiscal_end = today.replace(month=12, day=31)
	fiscal_start_str = fiscal_start.strftime("%Y-%m-%d")
	fiscal_end_str = fiscal_end.strftime("%Y-%m-%d")

	month_start = get_first_day(today)
	month_end = get_last_day(today)

	# 2. Employees to process
	employees = frappe.db.sql(
		"""
		SELECT name, employee_name, date_of_joining
		FROM `tabEmployee`
		WHERE status = 'Active'
		  AND employment_type NOT IN ('Armed Forces', 'GCE')
		""",
		as_dict=True,
	)
	
	leave_type = "Earned Leave"
	monthly_credit = 2.5

	for e in employees:
		doj = getdate(e.date_of_joining)
		if doj > fiscal_end:
			continue

		# 3. Get or create ONE Leave Allocation for this fiscal year
		alloc_from = max(doj, fiscal_start)
		alloc_to = fiscal_end

		la_row = frappe.db.get_value(
			"Leave Allocation",
			{
				"employee": e.name,
				"leave_type": leave_type,
				"from_date": alloc_from,
				"to_date": alloc_to,
				"docstatus": 1,
			},
			["name"],
			as_dict=True,
		)

		if la_row:
			la_name = la_row.name
		else:
			la = frappe.new_doc("Leave Allocation")
			la.employee = e.name
			la.employee_name = e.employee_name
			la.leave_type = leave_type
			la.from_date = alloc_from
			la.to_date = alloc_to
			la.carry_forward = cint(0)
			la.unused_leaves = 0
			la.new_leaves_allocated = 0
			la.insert()
			la.submit()
			la_name = la.name

			frappe.logger().info(
				f"[EL] Created fiscal-year Leave Allocation {la_name} for {e.name} "
				f"({alloc_from} to {alloc_to})"
			)
			#  CARRY-FORWARD FROM PREVIOUS YEAR
			prev_year = fiscal_start.year - 1
			prev_start = getdate(f"{prev_year}-01-01")
			prev_end = getdate(f"{prev_year}-12-31")

			closing_balance = get_leave_balance_on(
				e.name,
				leave_type,
				prev_end,
				to_date=prev_end,
				consider_all_leaves_in_the_allocation_period=True,
				for_consumption=False,
			)
			closing_balance = flt(closing_balance or 0)

			merged_cl_to_el = frappe.db.sql(
				"""
				SELECT COALESCE(SUM(leaves), 0)
				FROM `tabLeave Ledger Entry`
				WHERE employee = %s
				  AND leave_type = %s
				  AND transaction_type = 'Merge CL To EL'
				  AND docstatus = 1
				  AND from_date >= %s
				  AND to_date   <= %s
				""",
				(e.name, leave_type, prev_start, prev_end),
			)[0][0]
			merged_cl_to_el = flt(merged_cl_to_el or 0)
			carry_forward_total = closing_balance + merged_cl_to_el

			if carry_forward_total > 0:
				existing_cf = frappe.db.exists(
					"Leave Ledger Entry",
					{
						"employee": e.name,
						"leave_type": leave_type,
						"transaction_type": "Leave Allocation",
						"transaction_name": la_name,
						"from_date": fiscal_start,
						"to_date": fiscal_end,
						"is_carry_forward": 1,
						"docstatus": 1,
					},
				)

				if not existing_cf:
					cf_lle = frappe.new_doc("Leave Ledger Entry")
					cf_lle.employee = e.name
					cf_lle.employee_name = e.employee_name
					cf_lle.leave_type = leave_type
					cf_lle.from_date = fiscal_start
					cf_lle.to_date = fiscal_end
					cf_lle.leaves = carry_forward_total
					cf_lle.transaction_type = "Leave Allocation"
					cf_lle.transaction_name = la_name
					cf_lle.is_carry_forward = 1
					cf_lle.is_expired = 0
					cf_lle.insert(ignore_permissions=True)
					cf_lle.submit()

					frappe.logger().info(
						f"[EL] Carry forward for {e.name}: EL closing={closing_balance}, "
						f"merged CL→EL={merged_cl_to_el}, total CF={carry_forward_total}"
					)

		from_date = max(doj, month_start)
		to_date = month_end
		service_days = date_diff(to_date, from_date) + 1

		if service_days <= 14:
			frappe.logger().info(
				f"[EL] Skipping {e.name} for {from_date}–{to_date}, "
				f"service days = {service_days} (<= 14)"
			)
			continue

		existing_lle = frappe.db.get_value(
			"Leave Ledger Entry",
			{
				"employee": e.name,
				"leave_type": leave_type,
				"transaction_type": "Leave Allocation",
				"transaction_name": la_name,
				"from_date": from_date,
				"to_date": to_date,
			},
			["name", "docstatus"],
			as_dict=True,
		)

		if existing_lle and existing_lle.docstatus == 1:
			frappe.logger().info(
				f"[EL] Submitted LLE already exists for {e.name} "
				f"{from_date} to {to_date}, LA {la_name}. Skipping."
			)
			continue

		max_leaves_allowed = frappe.db.get_value(
			"Leave Type", leave_type, "max_leaves_allowed"
		)
		max_leaves_allowed = flt(max_leaves_allowed) if max_leaves_allowed else 0

		already_allocated_year = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(leaves), 0)
			FROM `tabLeave Ledger Entry`
			WHERE employee = %s
			  AND leave_type = %s
			  AND transaction_type = 'Leave Allocation'
			  AND transaction_name = %s
			  AND docstatus = 1
			  AND is_carry_forward = 0
			  AND from_date >= %s
			  AND to_date   <= %s
			""",
			(e.name, leave_type, la_name, fiscal_start_str, fiscal_end_str),
		)[0][0]

		if max_leaves_allowed and flt(already_allocated_year) + monthly_credit > max_leaves_allowed:
			frappe.logger().info(
				f"[EL] Allocation cap reached for {e.name}. "
				f"Current year NEW total: {already_allocated_year}, skipping this month."
			)
			continue

		if existing_lle and existing_lle.docstatus == 0:
			lle_doc = frappe.get_doc("Leave Ledger Entry", existing_lle.name)
			lle_doc.leaves = monthly_credit
			lle_doc.submit()

			frappe.logger().info(
				f"[EL] Draft LLE updated & submitted for {e.name}: "
				f"{from_date} to {to_date}, {monthly_credit} days, LA {la_name}"
			)
		else:
			lle_doc = frappe.new_doc("Leave Ledger Entry")
			lle_doc.employee = e.name
			lle_doc.employee_name = e.employee_name
			lle_doc.leave_type = leave_type
			lle_doc.from_date = from_date
			lle_doc.to_date = to_date
			lle_doc.leaves = monthly_credit
			lle_doc.transaction_type = "Leave Allocation"
			lle_doc.transaction_name = la_name
			lle_doc.is_carry_forward = 0
			lle_doc.is_expired = 0
			lle_doc.insert(ignore_permissions=True)
			lle_doc.submit()

			frappe.logger().info(
				f"[EL] LLE created for {e.name}: {from_date} to {to_date}, "
				f"{monthly_credit} days, LA {la_name}"
			)

		year_totals = frappe.db.sql(
			"""
			SELECT
				COALESCE(SUM(CASE WHEN is_carry_forward = 1 THEN leaves ELSE 0 END), 0) AS carry_forward_leaves,
				COALESCE(SUM(CASE WHEN is_carry_forward = 0 THEN leaves ELSE 0 END), 0) AS new_leaves
			FROM `tabLeave Ledger Entry`
			WHERE employee = %s
			  AND leave_type = %s
			  AND transaction_type = 'Leave Allocation'
			  AND transaction_name = %s
			  AND docstatus = 1
			  AND from_date >= %s
			  AND to_date   <= %s
			""",
			(e.name, leave_type, la_name, fiscal_start_str, fiscal_end_str),
			as_dict=True,
		)[0]

		cf_leaves = flt(year_totals.carry_forward_leaves)
		new_leaves = flt(year_totals.new_leaves)
		total_leaves = cf_leaves + new_leaves

		frappe.db.set_value(
			"Leave Allocation",
			la_name,
			{
				"unused_leaves": cf_leaves,
				"new_leaves_allocated": new_leaves,
				"total_leaves_allocated": total_leaves,
			},
		)

	return 1

# end

# reminder notitification fro contract renewal
def send_contract_renewal_reminders():
	today_date = getdate(nowdate())

	# Run only on 15th or last day of the month
	if today_date.day != 15 and today_date != get_last_day(today_date):
		return 0

	# Find next scheduler run date
	if today_date.day == 15:
		next_run_date = get_last_day(today_date)
	else:
		next_month_date = add_days(today_date, 1)
		next_run_date = getdate(f"{next_month_date.year}-{next_month_date.month}-15")

	# Check contract_end_date around 3 months before contract expiry
	contract_end_from = add_days(today_date, 90)
	contract_end_to = add_days(next_run_date, 90)
	allowed_employment_types = [
		"Regular Contract",
		"Consolidated Contract",
		"Deputation",
	]

	employees = frappe.get_all(
		"Employee",
		filters={
			"status": "Active",
			"employment_type": ["in", allowed_employment_types],
			"contract_end_date": ["between", [contract_end_from, contract_end_to]],
		},
		fields=[
			"name",
			"employee_name",
			"employment_type",
			"department",
			"designation",
			"contract_end_date",
			"user_id",
			"company_email",
			"personal_email",
		],
	)

	if not employees:
		frappe.logger().info(
			f"[Contract Renewal Reminder] No employees due between {contract_end_from} and {contract_end_to}"
		)
		return 0

	hr_group_email = "hr@gyalsunginfra.bt"

	for emp in employees:
		employee_email = emp.user_id or emp.company_email or emp.personal_email

		recipients = [hr_group_email]

		if employee_email:
			recipients.append(employee_email)

		recipients = list(set([r for r in recipients if r]))

		days_left = date_diff(emp.contract_end_date, today_date)

		subject = f"Contract Renewal Reminder: {emp.employee_name}"

		message = f"""
		Dear HR Team and {emp.employee_name},<br><br>

		This is a reminder that the employment contract for the following employee will expire in approximately <b>3 months</b>.<br><br>

		<b>Employee ID:</b> {emp.name}<br>
		<b>Employee Name:</b> {emp.employee_name}<br>
		<b>Employment Type:</b> {emp.employment_type or ''}<br>
		<b>Department:</b> {emp.department or ''}<br>
		<b>Designation:</b> {emp.designation or ''}<br>
		<b>Contract End Date:</b> {emp.contract_end_date}<br>
		<b>Days Remaining:</b> {days_left}<br><br>

		HR is requested to review and initiate the contract renewal process as required.<br><br>

		Regards,<br>
		ERP System
		"""

		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype="Employee",
			reference_name=emp.name,
			now=False,
		)

		frappe.logger().info(
			f"[Contract Renewal Reminder] Email queued for {emp.name} "
			f"to {', '.join(recipients)}. Contract End Date: {emp.contract_end_date}"
		)

	return 1

#function to get the difference between two dates
@frappe.whitelist()
def get_date_diff(start_date, end_date):
	if start_date is None:
		return 0
	elif end_date is None:
		return 0
	else:	
		return frappe.utils.data.date_diff(end_date, start_date) + 1

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

# ++++++++++++++++++++ VER#2.0#CDCL#886 BEGINS ++++++++++++++++++++
# VER#2.0#CDCL#886: Following code is commented by SHIV on 06/09/2018
'''		
# Ver 1.0 added by SSK on 03/08/2016, Fetching PF component
@frappe.whitelist()
def get_company_pf(fiscal_year=None, employee=None):
	employee_pf = frappe.db.get_single_value("HR Settings", "employee_pf")
	if not employee_pf:
		frappe.throw("Setup Employee PF in HR Settings")
	employer_pf = frappe.db.get_single_value("HR Settings", "employer_pf")
	if not employer_pf:
		frappe.throw("Setup Employer PF in HR Settings")
	health_contribution = frappe.db.get_single_value("HR Settings", "health_contribution")
	if not health_contribution:
		frappe.throw("Setup Health Contribution in HR Settings")
	retirement_age = frappe.db.get_single_value("HR Settings", "retirement_age")
	if not retirement_age:
		frappe.throw("Setup Retirement Age in HR Settings")
		result = ((flt(employee_pf), flt(employer_pf), flt(health_contribution), flt(retirement_age)),)
	return result

# Ver 1.0 added by SSK on 04/08/2016, Fetching GIS component
@frappe.whitelist()
def get_employee_gis(employee):
		#msgprint(employee);
		result = frappe.db.sql("""select a.gis
				from `tabEmployee Grade` a, `tabEmployee` b
				where b.employee = %s
				and b.employee_group = a.employee_group
				and b.grade = a.name
				limit 1
				""",employee);

		if result:
				return result[0][0]
		else:
				return 0.0
'''

# VER#2.0#CDCL#886: Following code is added by SHIV on 06/09/2018
@frappe.whitelist()
def get_payroll_settings(employee=None):
		settings = {}
		if employee:
				settings = frappe.db.sql("""
						select
								e.employee_group,
								e.grade,
								d.sws_contribution,
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
		# sws_type = frappe.db.get_single_value('HR Settings', 'sws_type')
		# settings.update({'sws_type': sws_type})
		return settings
# +++++++++++++++++++++ VER#2.0#CDCL#886 ENDS +++++++++++++++++++++

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

def get_officiating_employee(employee):
	# frappe.msgprint
	if not employee:
		frappe.throw("Employee is Mandatory")
		
	#return frappe.db.sql("select officiate from `tabOfficiating Employee` where docstatus = 1 and revoked != 1 and %(today)s between from_date and to_date and employee = %(employee)s order by creation desc limit 1", {"today": nowdate(), "employee": employee}, as_dict=True)
	qry = "select officiate from `tabOfficiating Employee` where docstatus = 1 and revoked != 1 and %(today)s between from_date and to_date and employee = %(employee)s order by creation desc limit 1"
	officiate = frappe.db.sql(qry, {"today": nowdate(), "employee": employee}, as_dict=True)

	if officiate:
		flag = True
		while flag:
			temp = frappe.db.sql(qry, {"today": nowdate(), "employee": officiate[0].officiate}, as_dict=True)
			if temp:
				officiate = temp
			else:
				flag = False
	return officiate

def update_suspension_record():
	query = "select employee, increment_month, promotion_month from `tabEmployee Disciplinary Record` where docstatus=1 and not_quilty_or_acquitted=0 and DATE_ADD(to_date, INTERVAL 1 DAY) = %(today)s"
	data = frappe.db.sql(query, {"today":nowdate()})
	for d in data:
		emp = frppe.get_doc("Employee", self.employee)
		emp.employment_status = "In Service"
		emp.increment_and_promotion_cycle = d.increment_month
		emp.promotion_cycle = d.promotion_month
		emp.save()
		
	
