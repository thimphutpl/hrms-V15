# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt, cstr


def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {
            "fieldname": "company",
            "label": _("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "width": 80,
        },
        {
            "fieldname": "cost_center",
            "label": _("Cost Center"),
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 120,
        },
        {
            "fieldname": "cost_center_number",
            "label": _("Cost Center Number"),
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "branch",
            "label": _("Branch"),
            "fieldtype": "Link",
            "options": "Branch",
            "width": 120,
        },
        {
            "fieldname": "fiscal_year",
            "label": _("Year"),
            "fieldtype": "Link",
            "options": "Fiscal Year",
            "width": 80,
        },
        {
            "fieldname": "month",
            "label": _("Month"),
            "fieldtype": "Data",
            "width": 80,
        },
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 100,
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 140,
        },
        {
            "fieldname": "designation",
            "label": _("Designation"),
            "fieldtype": "Link",
            "options": "Designation",
            "width": 120,
        },
        {
            "fieldname": "cid",
            "label": _("CID"),
            "fieldtype": "Data",
            "width": 110,
        },
        {
            "fieldname": "date_of_birth",
            "label": _("Date Of Birth"),
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "fieldname": "date_of_joining",
            "label": _("Date Of Joining"),
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "fieldname": "employee_group",
            "label": _("Group"),
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "fieldname": "employee_grade",
            "label": _("Grade"),
            "fieldtype": "Data",
            "width": 60,
        },
        {
          "fieldname": "ora",
          "label": _("ORAcNo"),
          "fieldtype": "Data",
          "width": 100
        },
        {
            "fieldname": "salary_saving_scheme",
            "label": _("Salary Saving Scheme"),
            "fieldtype": "Currency",
            "width": 120,
        }
    ]


def get_data(filters):
    conditions, filters = get_conditions(filters)

    return frappe.db.sql(
        """
        SELECT
            t1.company AS company,
            t1.cost_center AS cost_center,
            cc.cost_center_number AS cost_center_number,
            t1.branch AS branch,
            t1.fiscal_year AS fiscal_year,
            t1.month AS month,
            t1.employee AS employee,
            t3.employee_name AS employee_name,
            t1.designation AS designation,
            t3.passport_number AS cid,
            t3.date_of_birth AS date_of_birth,
            t3.date_of_joining AS date_of_joining,
            t3.employee_group AS employee_group,
            t1.employee_grade AS employee_grade,
            SUM(IFNULL(t2.amount, 0)) AS salary_saving_scheme,
            t3.department AS department,
            t2.reference_number as ora
        FROM `tabSalary Slip` t1
        INNER JOIN `tabSalary Detail` t2
            ON t2.parent = t1.name
        INNER JOIN `tabEmployee` t3
            ON t3.name = t1.employee
        INNER JOIN `tabCost Center` cc
            ON cc.name = t1.cost_center
        WHERE
            t1.docstatus = 1
            AND t3.employee_group != 'Temporary'
            AND t2.salary_component = 'Salary Saving Scheme'
            {conditions}
        GROUP BY
            t1.company,
            t1.cost_center,
            t1.branch,
            t1.fiscal_year,
            t1.month,
            t1.employee,
            t3.employee_name,
            t1.designation,
            t3.passport_number,
            t3.date_of_birth,
            t3.date_of_joining,
            t3.employee_group,
            t1.employee_grade
        ORDER BY
            t1.company,
            t1.cost_center,
            t1.branch,
            t1.employee
        """.format(conditions=conditions),
        filters,
        as_dict=True,
    )


def get_conditions(filters):
    conditions = ""

    if filters.get("month"):
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]

        month = filters["month"]

        if isinstance(month, str) and month in month_names:
            filters["month"] = month_names.index(month) + 1

        conditions += " AND t1.month = %(month)s"

    if filters.get("fiscal_year"):
        conditions += " AND t1.fiscal_year = %(fiscal_year)s"

    if filters.get("company"):
        conditions += " AND t1.company = %(company)s"

    if filters.get("employee"):
        conditions += " AND t1.employee = %(employee)s"
    if filters.get("cost_center"):
        conditions += " AND t1.cost_center = %(cost_center)s"

    return conditions, filters