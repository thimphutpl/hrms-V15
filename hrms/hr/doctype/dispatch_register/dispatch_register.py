# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class DispatchRegister(Document):

	def validate(self):
		self.generate_dispatch_no()
 
	def generate_dispatch_no(self):
		if self.manual_dispatch and self.dispatch_series_type:
			id = frappe.db.sql('''
						select dispatch_serial from `tabDispatch Register` where dispatch_series_type='{0}' and fiscal_year='{1}' and docstatus=1 order by creation desc limit 1;
						'''.format(self.dispatch_series_type,self.fiscal_year))
			if not id or not id[0][0]:
			    self.dispatch_serial = 1
			else:
				
				self.dispatch_serial = int(id[0][0]) + 1
				self.transaction_dispatch_number = f'{self.dispatch_series_type}{self.dispatch_serial}'
   
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
