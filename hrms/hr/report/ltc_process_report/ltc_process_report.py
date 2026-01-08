# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe

def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Sr No", "fieldname": "sr_no", "fieldtype": "Int", "width": 60},
        {"label": "Employee ID", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
        {"label": "TPN No", "fieldname": "tpn_number", "fieldtype": "Data", "width": 120},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 140},
        {"label": "Bank Name", "fieldname": "bank_name", "fieldtype": "Data", "width": 110},
        {"label": "A/C No", "fieldname": "account_no", "fieldtype": "Data", "width": 140},
        {"label": "Actual Amount", "fieldname": "actual_amount", "fieldtype": "Currency", "width": 120},
        {"label": "TDS Amount", "fieldname": "tds_amount", "fieldtype": "Currency", "width": 110},
        {"label": "Balance Amount", "fieldname": "balance_amount", "fieldtype": "Currency", "width": 130},
        
    ]


def get_data(filters):
    conditions = []
    values = {}

    if filters.get("fiscal_year"):
        conditions.append("ltc.fiscal_year = %(fiscal_year)s")
        values["fiscal_year"] = filters["fiscal_year"]

    if filters.get("processing_branch"):
        conditions.append("ltc.processing_branch = %(processing_branch)s")
        values["processing_branch"] = filters["processing_branch"]

    if filters.get("ltc_doc"):
        conditions.append("ltc.name = %(ltc_doc)s")
        values["ltc_doc"] = filters["ltc_doc"]

    if filters.get("from_date"):
        conditions.append("ltc.posting_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("ltc.posting_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    if filters.get("submitted_only", 1):
        conditions.append("ltc.docstatus = 1")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    rows = frappe.db.sql(f"""
        SELECT
            d.employee as employee,
            d.employee_name as employee_name,
            d.branch as branch,
            d.bank_name as bank_name,
            d.bank_ac_no as account_no,
            d.amount as actual_amount,
            e.tpn_number as tpn_no
        FROM `tabLeave Travel Concession` ltc
        INNER JOIN `tabLTC Details` d ON d.parent = ltc.name
        LEFT JOIN `tabEmployee` e ON e.name = d.employee
        WHERE {where_clause}
        ORDER BY ltc.posting_date DESC, d.branch, d.employee_name
    """, values, as_dict=True)

    data = []

    total_actual = 0
    total_tds = 0
    total_balance = 0

    for i, r in enumerate(rows, start=1):
        actual = r.get("actual_amount") or 0
        tds = 0  # if later you compute, replace here
        balance = actual - tds

        total_actual += actual
        total_tds += tds
        total_balance += balance

        data.append({
            "sr_no": i,
            "employee": r.employee,
            "employee_name": r.employee_name,
            "tpn_number": r.tpn_no,
            "branch": r.branch,
            "bank_name": r.bank_name,
            "account_no": r.account_no,
            "actual_amount": actual,
            "tds_amount": tds,
            "balance_amount": balance,
        })

    # ✅ Add Total Row at the end
    if data:
        data.append({
            "sr_no": None,
            "employee": "",
            "employee_name": "<b>Total</b>",
            "tpn_number": "",
            "branch": "",
            "bank_name": "",
            "account_no": "",
            "actual_amount": total_actual,
            "tds_amount": total_tds,
            "balance_amount": total_balance,
        })

    return data

