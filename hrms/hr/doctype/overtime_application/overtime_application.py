# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate,flt,cint,today,add_to_date,time_diff_in_hours,nowdate
from frappe.model.document import Document
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states
from datetime import datetime, timedelta

class OvertimeApplication(Document):
	def validate(self):
		
		validate_workflow_states(self)
		self.prevent_double_claim()
		self.validate_child_dates()
		self.prevent_time_overlap()
		self.set_month_and_fy_from_first_date()
		self.validate_dates()
		self.calculate_totals()
		self.validate_eligible_creteria()
		if self.workflow_state != "Approved":
			notify_workflow_states(self)
		self.processed = 0
		self.validate_total_claim_amount()

	

# class OvertimeApplication(Document):
# 	def validate(self):
# 		self.prevent_double_claim()
# 		self.validate_child_dates()
# 		self.prevent_time_overlap()

	# Automatically set month and fiscal year from first child table date added by Kinzang.N
	def set_month_and_fy_from_first_date(self):
		if not self.get("items"):
			return
		for row in self.get("items"):
			if row.date:
				date_obj = getdate(row.date)
				self.month = date_obj.strftime("%B")  # e.g., January
				fy = frappe.db.get_value(
                    "Fiscal Year",
                    {"year_start_date": ("<=", date_obj), "year_end_date": (">=", date_obj)},
                    "name",
                )
				self.fiscal_year = fy
				break  # only use the first date

    # Prevent duplicate OT in same month/fiscal year added by Kinzang.N
	def prevent_double_claim(self):
		if not self.employee or not self.get("items"):
			return
		date_info = []
		for row in self.get("items"):
			if not row.date:
				continue
			date = getdate(row.date)
			fiscal_year = frappe.db.get_value(
				"Fiscal Year",
				{"year_start_date": ("<=", date), "year_end_date": (">=", date)},
				"name",
            )
			month = date.strftime("%B")
			if fiscal_year and month:
				date_info.append((fiscal_year, month))
				
				date_info = list(set(date_info))
				for fiscal_year, month in date_info:
					existing = frappe.db.sql("""
					SELECT DISTINCT oa.name
                		FROM `tabOvertime Application` oa
                		INNER JOIN `tabOvertime Application Item` oad
                    	ON oa.name = oad.parent
                		WHERE oa.employee=%s
                  			AND oa.name != %s
                  			AND oa.docstatus < 2
                  			AND MONTH(oad.date) = MONTH(%s)
                  			AND YEAR(oad.date) = YEAR(%s)
                		LIMIT 1
            		""", (self.employee, self.name, date, date))
					
					if existing:
						frappe.throw(
                    f"Overtime Application <b>{existing[0][0]}</b> already exists "
                    f"for {month}, {fiscal_year}. Duplicate claims are not allowed."
                )

    # Ensure child table dates match month/fiscal year Added by Kinzang.N on 22/10/2025
	def validate_child_dates(self):
		if not self.month or not self.fiscal_year or not self.get("items"):
			return
		fy_doc = frappe.get_doc("Fiscal Year", self.fiscal_year)
		fy_start, fy_end = fy_doc.year_start_date, fy_doc.year_end_date
		for row in self.get("items"):
			if not row.date:
				continue
			date_obj = getdate(row.date)
			child_month = date_obj.strftime("%B")
			if child_month != self.month:
				frappe.throw(f"Row #{row.idx}: Date {row.date} is not in selected month {self.month}.")

			if not (fy_start <= date_obj <= fy_end):
				frappe.throw(f"Row #{row.idx}: Date {row.date} is outside Fiscal Year {self.fiscal_year}.")

    # Prevent overlapping time. added by Kinzang.N
	def prevent_time_overlap(self):
		if not self.employee or not self.get("items"):
			return
		
		
		
		def parse_datetime(date_str, time_val):
			"""Combine date and time into a datetime object.
       			Handles string (HH:MM / HH:MM:SS) and timedelta (ERPNext Time field)."""
			date_obj = getdate(date_str)


			# If Time field returns timedelta Added BY Kinzang.n
			if isinstance(time_val, timedelta):
				hours = time_val.seconds // 3600
				minutes = (time_val.seconds % 3600) // 60
				seconds = time_val.seconds % 60
				t = datetime.strptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}", "%H:%M:%S").time()
				return datetime.combine(date_obj, t)

        # If string
			if isinstance(time_val, str):
				for fmt in ("%H:%M:%S", "%H:%M"):
					try:
						t = datetime.strptime(time_val, fmt).time()
						return datetime.combine(date_obj, t)
					except ValueError:
						continue
			frappe.throw(f"Invalid time format: {time_val}")


			# for fmt in ("%H:%M:%S", "%H:%M"):
			# 	try:
			# 		t = datetime.strptime(time_val, fmt).time()
			# 		return datetime.combine(date_obj, t)
			# 	except ValueError:
			# 		continue
			# frappe.throw(f"Invalid time format: {time_val}")
				
				# Store already processed times in current doc
				# 
		times_by_date = {}
		for row in self.get("items"):
			if not row.date or not row.from_date or not row.to_date:
				continue
			new_from_dt = parse_datetime(row.date, row.from_date)
			new_to_dt = parse_datetime(row.date, row.to_date)
				
			if new_from_dt >= new_to_dt:
				frappe.throw(f"Row #{row.idx}: 'From Time' must be earlier than 'To Time'.")
					
					# Check overlap with DB
			existing_rows = frappe.db.sql("""
            	SELECT oad.date, oad.from_date, oad.to_date, oa.name
            	FROM `tabOvertime Application Item` oad
            	INNER JOIN `tabOvertime Application` oa ON oa.name = oad.parent
            	WHERE oa.employee=%s
              		AND oa.name != %s
              		AND oa.docstatus < 2
              		AND oad.date=%s
        	""", (self.employee, self.name, row.date), as_dict=True)
				
			for ex in existing_rows:
				ex_from_dt = parse_datetime(ex["date"], ex["from_date"])
				ex_to_dt = parse_datetime(ex["date"], ex["to_date"])
					
				#Check if times overlap
				if new_from_dt < ex_to_dt and new_to_dt > ex_from_dt:
					frappe.throw(
						f"Row #{row.idx}: Time {row.from_date}-{row.to_date} overlaps with "
						f"existing overtime {ex['from_date']}-{ex['to_date']} in {ex['name']}."
					)

        	# Check overlap within same document
			date_key = row.date
			if date_key not in times_by_date:
				times_by_date[date_key] = []

			for f, t, idx in times_by_date[date_key]:
				if new_from_dt < t and new_to_dt > f:
					frappe.throw(
						f"Row #{row.idx}: Time {row.from_date}-{row.to_date} overlaps with "
						f"Row #{idx} in the same document."
                	)
			times_by_date[date_key].append((new_from_dt, new_to_dt, row.idx))

## till here for code added

	def validate_total_claim_amount(self):
		if self.total_amount and flt(self.total_amount) <= 0:
			frappe.throw("Total Claim Amount cannot be 0, please process again")

	def validate_eligible_creteria(self):
		if "Employee" not in frappe.get_roles(frappe.session.user):
			frappe.msgprint(_("Only employee of {} can apply for Overtime").format(frappe.bold(self.company)), title="Not Allowed", indicator="red", raise_exception=1)

		salary_struc=frappe.db.sql("select name from `tabSalary Structure` where employee='{}' and is_active='Yes'".format(self.employee), as_dict=True)[0].name
		if not salary_struc:
			frappe.throw("There is no salary strcuture for the employee ")

		if cint(frappe.db.get_value('Salary Structure',salary_struc,'eligible_for_overtime_and_payment')) == 0:
			frappe.msgprint(_("You are not eligible for overtime"), title="Not Eligible", indicator="red", raise_exception=1)

	def calculate_totals(self):			
		settings = frappe.get_single("HR Settings")
		overtime_limit_type, overtime_limit = settings.overtime_limit_type, flt(settings.overtime_limit)
		total_amount = 0
		total_hours = 0
		base_hourly_rate = None
		
		for i in self.get("items"):
			if i.is_holiday:
				i.is_late_night_ot = 0
			if not i.is_late_night_ot and not i.is_holiday and not base_hourly_rate:
				base_hourly_rate = flt(i.rate)	
			# i.rate = self.rate
			if i.is_late_night_ot or i.is_holiday:
				i.number_of_hours    = flt(time_diff_in_hours(i.to_date, i.from_date),2)
				i.amount             = flt(i.number_of_hours) * flt(flt(i.rate))
			else:
				i.number_of_hours    = flt(time_diff_in_hours(i.to_date, i.from_date),2)
				i.amount             = flt(i.number_of_hours) * flt(i.rate)
				
			total_hours += flt(i.number_of_hours)
			# if flt(i.number_of_hours) > flt(overtime_limit):
			# 	frappe.throw(_("Row#{}: Number of Hours cannot be more than {} hours").format(i.idx, overtime_limit))

			# if overtime_limit_type == "Per Day":
			# 	month_start_date = add_to_date(i.to_date, days=-1)
			# elif overtime_limit_type == "Per Month":
			# 	month_start_date = add_to_date(i.to_date, months=-1)
			# elif overtime_limit_type == "Per Year":
			# 	month_start_date = add_to_date(i.to_date, years=-1)
			# i.amount = flt(i.rate) * flt(i.number_of_hours)
			total_amount += i.amount
			
			
		self.actual_hours = flt(total_hours)
		# if flt(total_hours) > flt(overtime_limit):
		# 	frappe.throw(_("Only {} hours accepted for payment").format(overtime_limit))
		# 	self.total_hours = flt(overtime_limit)
		# 	self.total_hours_lapsed = flt(total_hours) - flt(overtime_limit)
		# else:
		self.total_hours = flt(self.actual_hours)
		self.total_amount = round(total_amount,0)
		self.actual_amount = round(total_amount,0)
		if base_hourly_rate:
			self.rate = round(base_hourly_rate, 0)
		# self.rate = round(total_rate, 0)

	def on_cancel(self):
		# notify_workflow_states(self)
		self.update_salary_structure(True)

	# def on_submit(self):
	# 	self.update_salary_structure()
		
		# notify_workflow_states(self)
	def update_salary_structure(self, cancel=False):
		if cancel:
			rem_list = []
			if self.salary_structure:
				doc = frappe.get_doc("Salary Structure", self.salary_structure)
				for d in doc.get("earnings"):
					if d.salary_component == self.salary_component and self.name in (d.reference_number, d.ref_docname):
						rem_list.append(d)

				[doc.remove(d) for d in rem_list]
				doc.save(ignore_permissions=True)
		else:
			if frappe.db.exists("Salary Structure", {"employee": self.employee, "is_active": "Yes"}):
				doc = frappe.get_doc("Salary Structure", {"employee": self.employee, "is_active": "Yes"})
				row = doc.append("earnings",{})
				row.salary_component        = "Overtime Allowance"
				# row.from_date               = self.recovery_start_date
				# row.to_date                 = self.recovery_end_date
				row.amount                  = flt(self.total_amount)
				row.default_amount          = flt(self.total_amount)
				row.reference_number        = self.name
				row.ref_docname             = self.name
				row.total_days_in_month     = 0
				row.working_days            = 0
				row.leave_without_pay       = 0
				row.payment_days            = 0
				doc.save(ignore_permissions=True)
				# self.db_set("salary_structure", doc.name)
			else:
				frappe.throw(_("No active salary structure found for employee {0} {1}").format(self.employee, self.employee_name), title="No Data Found")

	# Dont allow duplicate dates
	def validate_dates(self):				
		self.posting_date = nowdate()
				  
		for a in self.items:
			if not a.date:
				frappe.throw(_("Row#{0} : Date cannot be blank").format(a.idx),title="Invalid Date")

			if str(a.date) > str(nowdate()):
				frappe.throw(_("Row#{0} : Future dates are not accepted").format(a.idx), title="Invalid Date")

			#Validate if time interval falls between another time interval for the same date   
			for b in self.items:
				if a.date == b.date and a.idx != b.idx:
					time_format = "%H:%M:%S"
					# start1 = datetime.strptime(a.from_date, time_format)
					# end1 = datetime.strptime(a.to_date, time_format)
					# start2 = datetime.strptime(b.from_date, time_format)
					# end2 = datetime.strptime(b.to_date, time_format)
					start1 = datetime.strptime(str(a.from_date), time_format)
					end1 = datetime.strptime(str(a.to_date), time_format)
					start2 = datetime.strptime(str(b.from_date), time_format)
					end2 = datetime.strptime(str(b.to_date), time_format)

					#frappe.throw("{}, {}, {} and {},{},{}".format(start2,start1,end2,start2,end1,end2))
					# if start2 <= start1 <= end2 or start2 <= end1 <= end2:
					# 	frappe.throw("Duplicate Dates in row " + str(a.idx) + " and " + str(b.idx))

def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	user_roles = frappe.get_roles(user)

	if user == "Administrator":
		return
	if "HR User" in user_roles or "HR Manager" in user_roles:
		return

	return """(
		`tabOvertime Application`.owner = '{user}'
		or
		exists(select 1
				from `tabEmployee`
				where `tabEmployee`.name = `tabOvertime Application`.employee
				and `tabEmployee`.user_id = '{user}')
		or
		(`tabOvertime Application`.approver = '{user}' and `tabOvertime Application`.workflow_state not in ('Draft','Approved','Rejected','Cancelled'))
	)""".format(user=user)