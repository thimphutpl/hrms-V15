# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import datetime
from frappe.model.document import Document


class test(Document):
	def validate(self):
		self.check_attendnce_exit()
		self.get_office_goble_ip()
		self.get_signIn_time()
		self.get_signOut_time()
		
		# if self.sign_ip==""
		# frappe.throw(f"ip ={self.sign_ip}")

	def check_attendnce_exit(self):
		existing = frappe.db.sql("""
        SELECT name 
        FROM `tabtest`
        WHERE employee = %s
        AND DATE(creation) = CURDATE()
        AND name <> %s
        AND docstatus < 2
			""",(self.employee, self.name),as_dict=True)
			
		if existing:
			frappe.throw("record already exists for employee")
				
	def get_office_goble_ip(self):
		gobal_ip=frappe.db.get_single_value("HR Settings", "office_gobal_ip")
		ip=self.sign_ip
		start_ip = frappe.db.get_single_value("HR Settings", "office_local_start_ip")

		end_ip = frappe.db.get_single_value("HR Settings", "office_local_end_ip")
		check_ip=self.is_ip_in_range(ip, start_ip, end_ip)
		#frappe.throw(str(frappe.request.headers.get("X-Forwarded-For", "").split(",")[0].strip()))
		if frappe.request.headers.get("X-Forwarded-For", "").split(",")[0].strip():
			if gobal_ip != self.sign_ip:
				frappe.throw("you not in offices network")

		elif rappe.request.headers.get("X-Real-IP", ""):
			if not check_ip:
				frappe.throw("you not in offices network")
		else:
			frappe.throw("you not in offices network")


		

	def get_signIn_time(self):
		if self.workflow_state=="Draft":
			start_time = frappe.db.get_value("Shift Type","General", "start_time")
			current_time = datetime.datetime.now().time()
			base_date = datetime.datetime(1900, 1, 1)
			shift_start_time = (base_date + start_time).time()
			if shift_start_time < datetime.datetime.now().time():
				frappe.throw("Youhabe late")
		if self.workflow_state=="Sigin In":
			
			self.signout_time="00:00:00"

	def get_signOut_time(self):
		if self.workflow_state=="Sign Out":
			end_time = frappe.db.get_value("Shift Type","General", "end_time")
			current_time = datetime.datetime.now().time()
			base_date = datetime.datetime(1900, 1, 1)
			shift_end_time = (base_date + end_time).time()
			#frappe.throw(str(shift_end_time))
			if shift_end_time > datetime.datetime.now().time():
				frappe.throw("Youhabe late")
			#frappe.throw("pl")
			self.signout_time=datetime.datetime.now()
			self.status="Present"

	def is_ip_in_range(self,ip, start_ip, end_ip):
		import ipaddress
		ip = ipaddress.IPv4Address(ip)
		start = ipaddress.IPv4Address(start_ip)
		end = ipaddress.IPv4Address(end_ip)
		return start <= ip <= end

def make_travel_advance():
	print("hi pem")