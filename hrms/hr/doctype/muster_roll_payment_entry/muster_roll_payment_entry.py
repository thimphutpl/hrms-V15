# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from frappe.query_builder.functions import Coalesce, Count, Sum
from frappe.utils import (
	DATE_FORMAT,
	add_days,
	add_to_date,
	cint,
	comma_and,
	date_diff,
	flt,
	get_link_to_form,
	getdate,
	get_last_day,
	nowdate
)


class MusterRollPaymentEntry(Document):
	def onload(self):
		if not self.docstatus == 1 or self.pay_slips_submitted:
			return

		# check if pay slips were manually submitted
		entries = frappe.db.count("Pay Slip", {"muster_roll_payment_entry": self.name, "docstatus": 1}, ["name"])
		if cint(entries) == len(self.employees):
			self.set_onload("submitted_ss", True)

	def validate(self):
		self.set_status()

	def before_submit(self):
		self.validate_existing_pay_slips()
		# if self.get_employees_with_unmarked_attendance():
		# 	frappe.throw(_("Cannot submit. Attendance is not marked for some mr employees."))
		
	def on_submit(self):
		self.set_status(update=True, status="Submitted")
		self.create_pay_slips()

	def on_cancel(self):
		self.ignore_linked_doctypes = ("GL Entry", "Pay Slip", "Journal Entry")

		self.delete_linked_pay_slips()
		self.cancel_linked_journal_entries()

		# reset flags & update status
		self.db_set("pay_slips_created", 0)
		self.db_set("pay_slips_submitted", 0)
		self.set_status(update=True, status="Cancelled")
		# self.db_set("error_message", "")

	# def cancel(self):
	# 	pass

	def validate_existing_pay_slips(self):
		if not self.employees:
			return

		existing_pay_slips = []
		SalarySlip = frappe.qb.DocType("Pay Slip")

		existing_salary_slips = (
			frappe.qb.from_(SalarySlip)
			.select(SalarySlip.employee, SalarySlip.name)
			.where(
				(SalarySlip.employee.isin([emp.employee for emp in self.employees]))
				& (SalarySlip.fiscal_year == self.fiscal_year)
				& (SalarySlip.month == self.month)
				& (SalarySlip.docstatus != 2)
			)
		).run(as_dict=True)

		if len(existing_salary_slips):
			msg = _("Salary Slip already exists for {0} for the given dates").format(
				comma_and([frappe.bold(d.employee) for d in existing_salary_slips])
			)
			msg += "<br><br>"
			msg += _("Reference: {0}").format(
				comma_and([get_link_to_form("Salary Slip", d.name) for d in existing_salary_slips])
			)
			frappe.throw(
				msg,
				title=_("Duplicate Entry"),
			)

	def set_status(self, status=None, update=False):
		if not status:
			status = {0: "Draft", 1: "Submitted", 2: "Cancelled"}[self.docstatus or 0]

		if update:
			self.db_set("status", status)
		else:
			self.status = status

	def delete_linked_pay_slips(self):
		pay_slips = self.get_linked_pay_slips()
		# frappe.throw(str(pay_slips))

		# cancel & delete pay slips
		for pay_slip in pay_slips:
			if pay_slip.docstatus == 1:
				frappe.get_doc("Pay Slip", pay_slip.name).cancel()
			frappe.delete_doc("Pay Slip", pay_slip.name)

	def get_linked_pay_slips(self):
		return frappe.get_all("Pay Slip", {"muster_roll_payment_entry": self.name}, ["name", "docstatus"])

	def cancel_linked_journal_entries(self):
		journal_entries = frappe.get_all(
			"Journal Entry Account",
			{"reference_type": self.doctype, "reference_name": self.name, "docstatus": 1},
			pluck="parent",
			distinct=True,
		)

		# cancel Journal Entries
		for je in journal_entries:
			frappe.get_doc("Journal Entry", je).cancel()

	@frappe.whitelist()
	def fill_employee_details(self):
		
		filters = frappe._dict(
			company=self.company,
			fiscal_year=self.fiscal_year,
			month=self.month
		)
		employees = get_muster_roll_employee_list(filters, as_dict=True)
		self.set("employees", [])

		if not employees:
			error_msg = _(
				"No employees found for the mentioned criteria:<br>Company: {0}"
			).format(
				frappe.bold(self.company),
			)
			# if self.branch:
			# 	error_msg += "<br>" + _("Branch: {0}").format(frappe.bold(self.branch))
			if self.fiscal_year:
				error_msg += "<br>" + _("Fiscal Year: {0}").format(frappe.bold(self.fiscal_year))
			if self.month:
				error_msg += "<br>" + _("Month: {0}").format(frappe.bold(self.month))
			frappe.throw(error_msg, title=_("No employees found"))

		self.set("employees", employees)

		return self.get_employees_with_unmarked_attendance()

	@frappe.whitelist()
	def get_employees_with_unmarked_attendance(self) -> list[dict] | None:
		unmarked_attendance = []
		employee_details = self.get_employee_and_attendance_details()
		# default_holiday_list = frappe.db.get_value(
		# 	"Company", self.company, "default_holiday_list", cache=True
		# )

		for emp in self.employees:
			details = next((record for record in employee_details if record.name == emp.employee), None)
			if not details:
				continue

			start_date, end_date = self.get_payment_dates_for_employee(details)
			# holidays = self.get_holidays_count(
			# 	details.holiday_list or default_holiday_list, start_date, end_date
			# )
			payment_days = date_diff(end_date, start_date) + 1
			marked_days = details.attendance_count
			unmarked_days = payment_days - (details.attendance_count)

			if unmarked_days > 0:
				unmarked_attendance.append(
					{
						"employee": emp.employee,
						"employee_name": emp.employee_name,
						"marked_days": marked_days,
						"unmarked_days": unmarked_days,
					}
				)
		
		return unmarked_attendance

	def get_employee_and_attendance_details(self) -> list[dict]:
		"""Returns a list of employee and attendance details like
		[
		        {
		                "name": "HREMP00001",
		                "date_of_joining": "2019-01-01",
		                "relieving_date": "2022-01-01",
		                "holiday_list": "Holiday List Company",
		                "attendance_count": 22
		        }
		]
		"""
		employees = [emp.employee for emp in self.employees]

		Employee = frappe.qb.DocType("Muster Roll Employee")
		Attendance = frappe.qb.DocType("Muster Roll Attendance")

		return (
			frappe.qb.from_(Employee)
			.left_join(Attendance)
			.on(
				(Employee.name == Attendance.employee)
				& (Attendance.attendance_date.between(self.start_date, self.end_date))
				& (Attendance.docstatus == 1)
			)
			.select(
				Employee.name,
				Employee.date_of_joining,
				Employee.relieving_date,
				Employee.holiday_list,
				Count(Attendance.name).as_("attendance_count"),
			)
			.where(Employee.name.isin(employees))
			.groupby(Employee.name)
		).run(as_dict=True)

	def get_payment_dates_for_employee(self, employee_details: dict) -> tuple[str, str]:
		start_date = self.start_date
		if employee_details.date_of_joining > getdate(self.start_date):
			start_date = employee_details.date_of_joining

		end_date = self.end_date
		if employee_details.relieving_date and employee_details.relieving_date < getdate(self.end_date):
			end_date = employee_details.relieving_date

		return start_date, end_date

	@frappe.whitelist()
	def create_pay_slips(self):
		self.check_permission("write")
		employees = [emp.employee for emp in self.employees]

		if employees:
			args = frappe._dict(
				{
					"company": self.company,
					"fiscal_year": self.fiscal_year,
					"month": self.month,
					"muster_roll_payment_entry": self.name,
					"start_date": self.start_date,
					"end_date": self.end_date,
				}
			)
			if len(employees) > 30:
				self.db_set("status", "Queued")
				frappe.enqueue(
					create_pay_slips_for_employees,
					timeout=3000,
					employees=employees,
					args=args,
					publish_progress=False,
				)
				frappe.msgprint(
					_("Pay Slip creation is queued. It may take a few minutes"),
					alert=True,
					indicator="blue",
				)
			else:
				create_pay_slips_for_employees(employees, args, publish_progress=False)
				# since this method is called via frm.call this doc needs to be updated manually
				self.reload()

	def get_pay_slip_list(self, ps_status, as_dict=False):
		"""
		Returns list of pay slips based on selected criteria
		"""

		ps = frappe.qb.DocType("Pay Slip")
		ps_list = (
			frappe.qb.from_(ps)
			.select(ps.name)
			.where(
				(ps.docstatus == ps_status)
				& (ps.fiscal_year == self.fiscal_year)
				& (ps.month == self.month)
				& (ps.muster_roll_payment_entry == self.name)
				& ((ps.journal_entry.isnull()) | (ps.journal_entry == ""))
			)
		).run(as_dict=as_dict)

		return ps_list

	@frappe.whitelist()
	def submit_pay_slips(self):
		self.check_permission("write")
		pay_slips = self.get_pay_slip_list(ps_status=0)

		if len(pay_slips) > 30:
			self.db_set("status", "Queued")
			frappe.enqueue(
				submit_pay_slips_for_employees,
				timeout=3000,
				payroll_entry=self,
				pay_slips=pay_slips,
				publish_progress=False,
			)
			frappe.msgprint(
				_("Pay Slip submission is queued. It may take a few minutes"),
				alert=True,
				indicator="blue",
			)
		else:
			submit_pay_slips_for_employees(self, pay_slips, publish_progress=False)

	@frappe.whitelist()
	def has_bank_entries(self) -> dict[str, bool]:
		je = frappe.qb.DocType("Journal Entry")
		jea = frappe.qb.DocType("Journal Entry Account")

		bank_entries = (
			frappe.qb.from_(je)
			.inner_join(jea)
			.on(je.name == jea.parent)
			.select(je.name)
			.where(
				(je.voucher_type == "Bank Entry")
				& (jea.reference_name == self.name)
				& (jea.reference_type == "Muster Roll Payment Entry")
			)
		).run(as_dict=True)

		return {
			"has_bank_entries": bool(bank_entries)
		}

	@frappe.whitelist()
	def make_bank_entry(self):
		"""
			---------------------------------------------------------------------------------
			type            Dr            Cr               voucher_type
			------------    ------------  -------------    ----------------------------------
			to payables     earnings      deductions       journal entry (journal voucher)
			to bank         net pay       bank             bank entry (bank payment voucher)
			---------------------------------------------------------------------------------
		"""
		self.check_permission("write")

		company = frappe.db.get("Company", self.company)
		company_cc 				= company.get("cost_center")
		default_bank_account	= frappe.db.get_value("Branch", self.processing_branch, "expense_bank_account")
		default_payable_account	= company.get("default_payroll_payable_account")
		expense_account 		= company.get("travel_advance_account")

		pay_slip_total = 0
		pay_details = self.get_pay_slip_details()

		posting = frappe._dict()
		for pay_detail in pay_details:
			posting.setdefault("to_payables", []).append({
				"account" 					: expense_account,
				"debit_in_account_currency"	: flt(pay_detail.net_pay),
				"cost_center"    			: pay_detail.cost_center,
				"reference_type"			: self.doctype,
				"reference_name"			: self.name,
			})
			pay_slip_total += flt(pay_detail.net_pay)
		
		# To Bank
		if posting.get("to_payables") and len(posting.get("to_payables")):
			posting.setdefault("to_bank", []).append({
				"account"       				: default_payable_account,
				"debit_in_account_currency"		: flt(pay_slip_total),
				"cost_center"   				: company_cc,
				"party_check"   				: 0,
				"reference_type"				: self.doctype,
				"reference_name"				: self.name,
			})
			posting.setdefault("to_bank", []).append({
				"account"       				: default_bank_account,
				"credit_in_account_currency"	: flt(pay_slip_total),
				"cost_center"   				: company_cc,
				"party_check"   				: 0,
				"reference_type"				: self.doctype,
				"reference_name"				: self.name,
			})
			posting.setdefault("to_payables",[]).append({
				"account"       				: default_payable_account,
				"credit_in_account_currency" 	: flt(pay_slip_total),
				"cost_center"  				 	: company_cc,
				"party_check"   				: 0,
				"reference_type"				: self.doctype,
				"reference_name"				: self.name,
			})

		if posting:
			jv_name, v_title = None, ""
			for i in posting:
				if i == "to_payables":
					v_title         = "To Payables"
					v_voucher_type  = "Journal Entry"
					v_naming_series = "Journal Voucher"
				else:
					v_title         = "To Bank" if i == "to_bank" else i
					v_voucher_type  = "Bank Entry"
					v_naming_series = "Bank Payment Voucher"

				if v_title:
					v_title = "Payment "+str(self.fiscal_year)+'- '+str(self.month)+" - "+str(v_title)
				else:
					v_title = "Payment "+str(self.fiscal_year)+'- '+str(self.month)

				doc = frappe.get_doc({
						"doctype"			: "Journal Entry",
						"voucher_type"		: v_voucher_type,
						"naming_series"		: v_naming_series,
						"title"				: v_title,
						"fiscal_year"		: self.fiscal_year,
						"remark"			: v_title,
						"posting_date"		: nowdate(),                     
						"company"			: self.company,
						"accounts"			: sorted(posting[i], key=lambda item: item['cost_center']),
						"branch"			: self.processing_branch,
						"reference_type"	: self.doctype,
						"reference_name"	: self.name,
					})
				doc.flags.ignore_permissions = 1 
				doc.insert()

				if i == "to_payables":
					doc.submit()
					jv_name = doc.name

			frappe.msgprint(_("Payment posting to accounts is successful."), title="Posting Successful")
		else:
			frappe.throw(_("No data found"), title="Posting failed")

	def get_pay_slip_details(self):
		PaySlip = frappe.qb.DocType("Pay Slip")

		return (
		frappe.qb.from_(PaySlip)
		.select(
			PaySlip.cost_center,
			Sum(PaySlip.total_earning).as_("total_earning"),
            Sum(PaySlip.net_pay).as_("net_pay")
		)
		.where(
			(PaySlip.docstatus != 2)
			& (PaySlip.company == self.company)
			& (PaySlip.muster_roll_payment_entry == self.name)
			& (PaySlip.fiscal_year == self.fiscal_year)
			& (PaySlip.month == self.month)
		).orderby(
			PaySlip.cost_center
		).groupby(
			PaySlip.cost_center
		)

	).run(as_dict=True)


def create_pay_slips_for_employees(employees, args, publish_progress=True):
	payment_entry = frappe.get_cached_doc("Muster Roll Payment Entry", args.muster_roll_payment_entry)

	try:
		pay_slips_exist_for = get_existing_pay_slips(employees, args)
		count = 0

		employees = list(set(employees) - set(pay_slips_exist_for))
		for emp in employees:
			args.update({"doctype": "Pay Slip", "employee": emp})
			frappe.get_doc(args).insert()

			count += 1
			if publish_progress:
				frappe.publish_progress(
					count * 100 / len(employees),
					title=_("Creating Pay Slips..."),
				)

		payment_entry.db_set({"status": "Submitted", "pay_slips_created": 1})

		if pay_slips_exist_for:
			frappe.msgprint(
				_(
					"Pay Slips already exist for employees {}, and will not be processed by this entry."
				).format(frappe.bold(", ".join(emp for emp in pay_slips_exist_for))),
				title=_("Message"),
				indicator="orange",
			)

	except Exception as e:
		frappe.db.rollback()
		# log_payroll_failure("creation", payroll_entry, e)

	finally:
		frappe.db.commit()
		# frappe.publish_realtime("completed_salary_slip_creation", user=frappe.session.user)
	

def get_existing_pay_slips(employees, args):
	PaySlip = frappe.qb.DocType("Pay Slip")

	return (
		frappe.qb.from_(PaySlip)
		.select(PaySlip.employee)
		.distinct()
		.where(
			(PaySlip.docstatus != 2)
			& (PaySlip.company == args.company)
			& (PaySlip.muster_roll_payment_entry == args.muster_roll_payment_entry)
			& (PaySlip.fiscal_year == args.fiscal_year)
			& (PaySlip.month == args.month)
			& (PaySlip.employee.isin(employees))
		)
	).run(pluck=True)

def submit_pay_slips_for_employees(payment_entry, pay_slips, publish_progress=True):
	try:
		submitted = []
		unsubmitted = []
		frappe.flags.via_payroll_entry = True
		count = 0

		for entry in pay_slips:
			pay_slip = frappe.get_doc("Pay Slip", entry[0])
			if pay_slip.net_pay < 0:
				unsubmitted.append(entry[0])
			else:
				try:
					pay_slip.submit()
					submitted.append(pay_slip)
				except frappe.ValidationError:
					unsubmitted.append(entry[0])

			count += 1
			if publish_progress:
				frappe.publish_progress(
					count * 100 / len(pay_slips), title=_("Submitting Pay Slips...")
				)

		if submitted:
			# payment_entry.make_accrual_jv_entry(submitted)
			payment_entry.db_set({"pay_slips_submitted": 1, "status": "Submitted"})

		show_payment_submission_status(submitted, unsubmitted, payment_entry)

	except Exception as e:
		frappe.db.rollback()
		# log_payroll_failure("submission", payroll_entry, e)

	finally:
		frappe.db.commit()
		# frappe.publish_realtime("completed_salary_slip_submission", user=frappe.session.user)

	# frappe.flags.via_payroll_entry = False

def show_payment_submission_status(submitted, unsubmitted, payment_entry):
	if not submitted and not unsubmitted:
		frappe.msgprint(
			_(
				"No pay slip found to submit for the above selected criteria OR pay slip already submitted"
			)
		)
	elif submitted and not unsubmitted:
		frappe.msgprint(
			_("Pay Slips submitted for period from {0} to {1}").format(
				payment_entry.fiscal_year, payment_entry.month
			),
			title=_("Success"),
			indicator="green",
		)
	elif unsubmitted:
		frappe.msgprint(
			_("Could not submit some Pay Slips: {}").format(
				", ".join(get_link_to_form("Pay Slip", entry) for entry in unsubmitted)
			),
			title=_("Failure"),
			indicator="red",
		)

def log_payment_failure(process, payment_entry, error):
	error_log = frappe.log_error(
		title=_("Pay Slip {0} failed for Payment Entry {1}").format(process, payment_entry.name)
	)
	message_log = frappe.message_log.pop() if frappe.message_log else str(error)

	try:
		if isinstance(message_log, str):
			error_message = json.loads(message_log).get("message")
		else:
			error_message = message_log.get("message")
	except Exception:
		error_message = message_log

	error_message += "\n" + _("Check Error Log {0} for more details.").format(
		get_link_to_form("Error Log", error_log.name)
	)

	payroll_entry.db_set({"error_message": error_message, "status": "Failed"})

def get_muster_roll_employee_list(filters, as_dict=True) -> list:
	emp_list = get_filtered_mr_employees(filters, as_dict=as_dict)

	if as_dict:
		employees_to_check = {emp.employee: emp for emp in emp_list}
	else:
		employees_to_check = {emp[0]: emp for emp in emp_list}

	return remove_payrolled_employees(employees_to_check, filters.fiscal_year, filters.month)

def get_filtered_mr_employees(filters, as_dict=False) -> list:
	Employee = frappe.qb.DocType("Muster Roll Employee")

	query = (
		frappe.qb.from_(Employee)
		.select(
			Employee.name.as_("employee"),
			Employee.employee_name,
			Employee.branch
		)
		.where(
			(Employee.status == "Active") 
			& (Employee.company == filters.company) 
		)
	)

	return query.run(as_dict=as_dict)

def remove_payrolled_employees(emp_list, fiscal_year, month):
	PaySlip = frappe.qb.DocType("Pay Slip")

	employees_with_payroll = (
		frappe.qb.from_(PaySlip)
		.select(PaySlip.employee)
		.where(
			(PaySlip.docstatus == 1)
			& (PaySlip.fiscal_year == fiscal_year)
			& (PaySlip.month == month)
		)
	).run(pluck=True)

	return [emp_list[emp] for emp in emp_list if emp not in employees_with_payroll]
