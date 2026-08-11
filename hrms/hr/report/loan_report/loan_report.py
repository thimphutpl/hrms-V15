from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, nowdate
from erpnext.accounts.utils import get_fiscal_year

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "loan_deduction_amount",
            "label": _("Loan Deduction Amount"),
            "fieldtype": "Currency",
            "width": 150
        },
        {
            "fieldname": "loan_start_date",
            "label": _("Loan Start Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "loan_end_date",
            "label": _("Loan End Date"),
            "fieldtype": "Date",
            "width": 120
        },
        {
            "fieldname": "Month",
            "label": _("Month"),
            "fieldtype": "Data",
            
            "width": 150
        }
        
    ]

def get_conditions(filters):
    conditions = []
    conditions.append("sd.salary_component = 'Financial Institution Loan'")
    conditions.append("sl.docstatus = 1")
    
    if filters.get("fiscal_year"):
        fiscal_year = filters.get("fiscal_year")
        fiscal_year_details = get_fiscal_year_details(fiscal_year)
        if fiscal_year_details:
            conditions.append("sl.posting_date BETWEEN %(start_date)s AND %(end_date)s")
            filters.update({
                "start_date": fiscal_year_details[0],
                "end_date": fiscal_year_details[1]
            })
    
    if filters.get("employee"):
        conditions.append("sl.employee = %(employee)s")
    
    if filters.get("employee_name"):
        conditions.append("sl.employee_name LIKE %(employee_name)s")
        filters["employee_name"] = "%" + filters["employee_name"] + "%"
        
    if filters.get("month"):
        conditions.append("sl.month =%(month)s")
    
    if filters.get("company"):
        conditions.append("sl.company = %(company)s")
    
    return conditions

def get_data(filters):
    conditions = get_conditions(filters)
    
    query = """
        SELECT 
            sl.employee,
            sl.employee_name,
            sd.amount as loan_deduction_amount,
            ssd.from_date as loan_start_date,
            ssd.to_date as loan_end_date,
            sl.month as Month
        FROM `tabSalary Detail` sd
        INNER JOIN `tabSalary Slip` sl ON sd.parent = sl.name
        INNER JOIN `tabSalary Structure` ss ON sl.salary_structure = ss.name
        INNER JOIN `tabSalary Detail` ssd ON ssd.parent = ss.name 
            AND ssd.salary_component = ''
            AND ssd.idx = sd.idx
    """
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY sl.employee, sl.posting_date DESC"
    
    data = frappe.db.sql(query, filters, as_dict=1)
    return data

def get_fiscal_year_details(fiscal_year):
    try:
        fiscal_year_doc = frappe.get_doc("Fiscal Year", fiscal_year)
        return [fiscal_year_doc.year_start_date, fiscal_year_doc.year_end_date]
    except frappe.DoesNotExistError:
        return None