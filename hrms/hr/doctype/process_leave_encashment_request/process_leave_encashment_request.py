# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ProcessLeaveEncashmentRequest(Document):
	def validate(self):
		self.check_duplicate_entry()
		self.get_leave_details_for_encashment()
		self.calculate_total_leave()
		self.calculate_encash_carry_leave()
		self.add_ref()
  
	def on_cancel(self):
		# Fetch all Leave Encashment Requests related to this Process Leave Encashment Request
		leave_encashment_requests = frappe.get_all(
			"Leave Encashment Request", 
			filters={"ref_id": self.name},
			fields=["name"]
		)
		
		# Delete each Leave Encashment Request
		for ler in leave_encashment_requests:
			try:
				# Fetch the Leave Encashment Request document
				leave_encashment_request = frappe.get_doc("Leave Encashment Request", ler.name)
				
				# Delete the document
				leave_encashment_request.delete()
				
				# Optionally log success
				frappe.log_error(f"Successfully deleted LER: {ler.name}")
			except Exception as e:
				# Handle any errors that occur during the deletion process
				frappe.log_error(f"Error deleting LER {ler.name}: {str(e)}")

	def check_duplicate_entry(self):
		check = frappe.db.sql('''
		SELECT 1 
		FROM `tabProcess Leave Encashment Request` 
		WHERE fiscal_year = %s AND leave_period = %s
		and docstatus=1
		''', (self.fiscal_year, self.leave_period))
	
		# Throw an error if a duplicate entry is found
		if check:
			frappe.throw(
				"Process Leave Encashment for fiscal year {0} and leave period {1} already created ".format(
					self.fiscal_year, self.leave_period
				)
			)
	def get_leave_details_for_encashment(self):
		# if not frappe.db.get_value("Leave Type", self.leave_type, 'allow_encashment'):
		# 	frappe.throw(_("Leave Type {0} is not encashable").format(self.leave_type))

		# for emp in self.items:
		# 	allocation = self.get_leave_allocation(emp.employee)
		# 	casual_leave_allocation = self.get_casual_leave_allocation(emp.employee)
		# 	if not allocation:
		# 		frappe.throw(_("No Leaves Allocated to Employee: {0} for Leave Type: {1}").format(emp.employee, self.leave_type))
		# 	if not casual_leave_allocationallocation:
		# 		frappe.throw(_("No Leaves Allocated to Employee: {0} for Leave Type: {1}").format(emp.employee, "Casual Leave"))


		# 	emp.leave_balance = get_leave_balance_on(employee=emp.employee, date=today(), \
		# 		to_date=today(), leave_type=self.leave_type, consider_all_leaves_in_the_allocation_period=True)
		# 	emp.casual_leave_balance = get_leave_balance_on(employee=emp.employee, date=today(), \
		# 		to_date=today(), leave_type="Casual Leave", consider_all_leaves_in_the_allocation_period=True)
			
		# 	emp.casual_leave_allocation = casual_leave_allocation.name
		# 	emp.leave_allocation = allocation.name
		
		for emp in self.items:
			
			casual= frappe.db.sql('''
								SELECT SUM(leaves) as casual  from  `tabLeave Ledger Entry` WHERE     docstatus = 1 and  employee=%s and 
        						from_date >= '2024-01-01' and leave_type="Casual Leave";
								''',(emp.employee), as_dict=True
			)
			if casual:
				emp.casual_leave_balance = casual[0]['casual']	
			
			earned = frappe.db.sql('''
								SELECT SUM(leaves) as earned  from  `tabLeave Ledger Entry` WHERE     docstatus = 1 and  employee=%s and 
        						from_date >= '2024-01-01' and leave_type="Earned Leave";
								''',(emp.employee), as_dict=True
			)
			
				
			if earned:	
				emp.earned_leave_balance = earned[0]['earned']
				
			
				
		return True
	def calculate_total_leave(self):
		for emp in self.items:
			emp.total_leave_balance = (emp.earned_leave_balance if emp.earned_leave_balance else 0)  + emp.casual_leave_balance
	def add_ref(self):
		for i in self.items:
			i.ref = self.name
	def calculate_encash_carry_leave(self):
		for emp in self.items:
			if emp.total_leave_balance > 30:
				emp.enchashable_days = 30
				emp.carry_forward_days = emp.total_leave_balance - 30
			else:
				emp.enchashable_days =  emp.total_leave_balance
				emp.carry_forward_days = 0
	def get_leave_allocation(self, employee=None):
		leave_allocation = frappe.db.sql("""select name, to_date, total_leaves_allocated, carry_forwarded_leaves_count from `tabLeave Allocation` where '{0}'
		between from_date and to_date and docstatus=1 and leave_type='{1}'
		and employee = '{2}'""".format(self.posting_date or getdate(nowdate()), self.leave_type, employee), as_dict=1)
		return leave_allocation[0] if leave_allocation else None
	def get_casual_leave_allocation(self, employee=None):
		leave_allocation = frappe.db.sql("""select name, to_date, total_leaves_allocated, carry_forwarded_leaves_count from `tabLeave Allocation` where '{0}'
		between from_date and to_date and docstatus=1 and leave_type='Casual Leave'
		and employee = '{2}'""".format(self.posting_date or getdate(nowdate()), self.leave_type, employee), as_dict=1)
		return leave_allocation[0] if leave_allocation else None

	@frappe.whitelist()
	def get_employees(self):
		# if not self.leave_period or not self.leave_type:
		if not self.leave_period:
			frappe.throw("Either Leave Type/Leave Period is missing")
		
		self.set('items', [])
		query = """
				select e.name as employee, e.employee_name
				from `tabEmployee` e where status = 'Active'
				and not exists(select 1 from `tabLeave Encashment Request` ler where e.name = ler.employee and ler.ref_id = '{}') 
		""".format(self.name)

		
		entries = frappe.db.sql(query, as_dict=True)
  
		# for entry in entries:
		# 	entry['ref'] = self.name
		self.set('items', entries)

	def create_leave_encashment_request(self):
		"""
			Creates salary slip for selected employees if already not created
		"""
		self.check_permission('write')
		self.created = 1
		emp_list = [d.employee for d in self.items]

		if emp_list:
			args = frappe._dict({
				"name": self.name
			})
			if len(emp_list) > 300:
				frappe.enqueue(create_ler_for_employees, timeout=600, employees=emp_list, args=args)
			else:
				create_ler_for_employees(emp_list, args, publish_progress=False)
				# since this method is called via frm.call this doc needs to be updated manually
				self.reload()
    
	@frappe.whitelist()
	def submit_leave_encashment_request(self):
		names = frappe.db.sql(
			'''
			SELECT name 
			FROM `tabLeave Encashment Request` 
			WHERE ref_id = '{}'
			'''.format(self.name), 
			as_dict=True
		)

		# Loop through the retrieved names and submit each document
		for record in names:
			try:
				# Fetch the document
				leave_encashment_request = frappe.get_doc('Leave Encashment Request', record['name'])
				
				# Submit the document
				leave_encashment_request.submit()
			except Exception as e:
				frappe.log_error(
					message=f"Error submitting Leave Encashment Request {record['name']}: {str(e)}",
					title="Leave Encashment Request Submission Error"
				)
		self.reload()
        
	# def create_ler_for_employees(self, doc):
	# 	count = 0
	# 	# Retrieve the "Process Leave Encashment Request" document using the current document's name
	# 	pler = frappe.get_doc("Process Leave Encashment Request", self.name)
		
	# 	# Loop through each employee in the 'items' child table
	# 	for emp in pler.get("items"):
	# 		if emp.employee:
	# 			try:
	# 				# Create the Leave Encashment Request document for each employee
	# 				ler = frappe.get_doc({
	# 					"doctype": "Leave Encashment Request",
	# 					"employee": emp.employee,
	# 					"employee_name": emp.employee_name,
	# 					"earned_leave_balance":emp.earned_leave_balance,
	# 					"casual_leave_balance":emp.casual_leave_balance,
	# 					"total_leave_balance":emp.total_leave_balance,
	# 					"encashment_days":emp.enchashable_days,
	# 					"carry_forward_days":emp.carry_forward_days,
	# 					"ref_id":emp.ref,
	# 					"leave_period":pler.get("leave_period"),
	# 					# Add any additional fields you need here
	# 				})
	# 				ler.insert()  # Insert the newly created LER document
					
	# 				# Log success for the specific employee (optional)
	# 				frappe.msgprint(f"Successfully created LER for {emp.employee}")

	# 			except Exception as e:
	# 				# Log any errors that occur during document creation
	# 				frappe.log_error(f"Error creating LER for {emp.employee}: {str(e)}")
				
	# 			# Increment count for each employee processed
	# 			count += 1
	# 			if count == 2:
	# 				break
	
	# 	return True

	@frappe.whitelist()
	def create_ler_for_employees(self):
		count = 0
		# Retrieve the "Process Leave Encashment Request" document using the current document's name
		pler = frappe.get_doc("Process Leave Encashment Request", self.name)

		# Loop through each employee in the 'items' child table
		for emp in pler.get("items"):
			if emp.employee:
				try:
					# Check if a Leave Encashment Request already exists with the same ref_id and leave_period
					existing_ler = frappe.db.exists("Leave Encashment Request", {
						"employee": emp.employee,
						"ref_id": emp.ref,
						"leave_period": pler.get("leave_period")
					})
					
					if existing_ler:
						# If the LER already exists, skip creating a new one for this employee
						frappe.msgprint(f"LER for employee {emp.employee} with ref_id {emp.ref} and leave_period {pler.get('leave_period')} already exists.")
						continue  # Skip this employee

					# Create the Leave Encashment Request document for each employee if it doesn't exist
					ler = frappe.get_doc({
						"doctype": "Leave Encashment Request",
						"employee": emp.employee,
						"employee_name": emp.employee_name,
						"earned_leave_balance": emp.earned_leave_balance,
						"casual_leave_balance": emp.casual_leave_balance,
						"total_leave_balance": emp.total_leave_balance,
						"encashment_days": emp.enchashable_days,
						"carry_forward_days": emp.carry_forward_days,
						"ref_id": emp.ref,
						"leave_period": pler.get("leave_period"),
						# Add any additional fields you need here
					})
					ler.insert()  # Insert the newly created LER document

					# Log success for the specific employee (optional)
					frappe.msgprint(f"Successfully created LER for {emp.employee}")

				except Exception as e:
					# Log any errors that occur during document creation
					frappe.throw(f"Error creating LER for {emp.employee}: {str(e)}")

				# Increment count for each employee processed
				count += 1
				# if count == 2:
				# 	break

		return True


def create_ler_for_employees(employees, args, title=None, publish_progress=True):
	ler_exists_for = get_existing_lers(employees, args)
	count=0
	successful = 0
	failed = 0
	pler = frappe.get_doc("Process Leave Encashment Request", args.name)
	# payroll_entry.set('employees_failed', [])
	refresh_interval = 25
	total_count = len(set(employees))
	for emp in pler.get("items"):
		if emp.employee in employees and emp.employee not in ler_exists_for:
			error = None
			args.update({
				"doctype": "Leave Encashment Request",
				"employee": emp.employee,
				"employee_name": emp.employee_name
			})
			try:
				ler = frappe.get_doc(args)
				ler.insert()
				# successful += 1
			except Exception as e:
				error = str(e)
				# failed += 1
			count+=1

			lerd = frappe.get_doc("LER Details", emp.name)
			lerd.db_set("ref", ler.name)
			if publish_progress:
				show_progress = 0
				if count <= refresh_interval:
					show_progress = 1
				elif refresh_interval > total_count:
					show_progress = 1
				elif count%refresh_interval == 0:
					show_progress = 1
				elif count > total_count-refresh_interval:
					show_progress = 1
				
				if show_progress:
					description = " Processing {}: ".format(ler.name if ss else emp.employee) + "["+str(count)+"/"+str(total_count)+"]"
					frappe.publish_progress(count*100/len(set(employees) - set(ler_exists_for)),
						title = title if title else _("Creating Leave Encashemnt Requests..."),
						description = description)
					pass
	# payroll_entry.db_set("salary_slips_created", 0 if failed else 1)
	# payroll_entry.db_set("successful", cint(payroll_entry.successful)+cint(successful))
	# payroll_entry.db_set("failed", cint(payroll_entry.number_of_employees)-(cint(payroll_entry.successful)))
	pler.reload()
 
def create_ler_for_employees(employees, args, title=None, publish_progress=True):
	count = 0
	total_count = len(set(employees))
	pler = frappe.get_doc("Process Leave Encashment Request", args.name)
	
	for emp in pler.get("items"):
		if emp.employee in employees:
			args.update({
				"doctype": "Leave Encashment Request",
				"employee": emp.employee,
				"employee_name": emp.employee_name
			})
			
			try:
				ler = frappe.get_doc(args)
				ler.insert()
			except Exception as e:
				frappe.log_error(f"Error creating LER for {emp.employee}: {str(e)}")
			
			count += 1
	return True
	# pler.reload()

def get_existing_lers(employees, args):
	return frappe.db.sql_list("""
		select distinct employee from `tabLeave Encashment Request`
		where docstatus!= 2 and company = %s
			and ref_id = %s
			and employee in (%s)
	""" % ('%s', '%s', ', '.join(['%s']*len(employees))),
		[args.company, args.name] + employees)
