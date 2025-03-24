# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DispatchRegister(Document):

	def validate(self):
		self.generate_dispatch_no()
	
	# def on_submit(self):
	# 	self.generate_dispatch_no()
  
	def generate_dispatch_no(self):
		if self.manual_dispatch and self.dispatch_series_type:
			id = frappe.db.sql('''
						select dispatch_serial from `tabDispatch Register` where docstatus=1 order by dispatch_serial desc limit 1;
						''')
			if not id or not id[0][0]:
			    self.dispatch_serial = 1
			else:
				
				self.dispatch_serial = int(id[0][0]) + 1
		if not self.transaction_dispatch_number:
			self.transaction_dispatch_number = f'{self.dispatch_series_type}/{self.dispatch_serial}'
			self.file_no = self.transaction_dispatch_number
   
@frappe.whitelist()
def get_employees_by_department(transaction_type, transaction):
	if transaction_type == "eNote":
		dispatch_no = frappe.db.sql('''
			SELECT enote_format as dispatch_number
			FROM `tabeNote`
			WHERE name = %s
		''', (transaction,), as_dict=True)

		# Return the result if found, else return None
		return dispatch_no[0]['dispatch_number'] if dispatch_no else None
	else :
		dispatch_no = frappe.db.sql(f'''
			SELECT dispatch_number
			FROM `tab{transaction_type}`
			WHERE name = %s
		''', (transaction,), as_dict=True)


		# Return the result if found, else return None
		return dispatch_no[0]['dispatch_number'] if dispatch_no else None

@frappe.whitelist()
def get_date_depart(company,date,user):
	fiscal_year = frappe.db.sql('''
                             select fy.name,fyc.company from `tabFiscal Year` fy inner join `tabFiscal Year Company` 
                             fyc on fy.name = fyc.parent where fyc.company="{}" 
                             and '{}' between fy.year_start_date and fy.year_end_date;
                             '''.format(company,date),as_dict=True)
	if not fiscal_year:
		frappe.throw("Fiscal Year for your company not set for this date")
	if user != "Administrator":
		id = frappe.db.sql('''
                     select name from `tabEmployee` where user_id='{}';
                     '''.format(user),as_dict=True)
		if not id:
			frappe.throw("You dont have employee id mapped with your user")
		

	return {
        # 'dispatch_number': dispatch_no[0]['dispatch_number'] if dispatch_no else None,
        'fiscal_year': fiscal_year[0].name,
        'employee_id': id[0]['name'] if id else None
    }
	
