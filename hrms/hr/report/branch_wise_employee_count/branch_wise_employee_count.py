# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data



import frappe
from frappe import _


# Custom employee DocTypes other than the standard Employee DocType.
OTHER_EMPLOYEE_TYPES = [
    {
        "doctype": "Muster Roll Employee",
        "fieldname": "muster_roll_employee",
        "label": "Muster Roll Employee",
        "active_status": "Active",
    },
    {
        "doctype": "DFG AND GFG",
        "fieldname": "dfg_and_gfg",
        "label": "DFG & GFG",
        "active_status": "Active",
    },
    {
        "doctype": "Foreign Labourer",
        "fieldname": "foreign_labourer",
        "label": "Foreign Labourer",
        "active_status": "At-Site",
    },
    {
        "doctype": "Open Air Prisoner",
        "fieldname": "open_air_prisoner",
        "label": "Open Air Prisoner",
        "active_status": "Active",
    },
    {
        "doctype": "Arm Force",
        "fieldname": "arm_force",
        "label": "Armed Force",
        "active_status": "Active",
    },
	{
        "doctype": "Operator",
        "fieldname": "operator",
        "label": "Operator",
        "active_status": "Active",
    },
]


def execute(filters=None):
    filters = frappe._dict(filters or {})

    validate_employee_fields()

    employment_types = get_employment_types(filters)
    columns = get_columns(employment_types)
    data = get_data(filters, employment_types)
    chart = get_chart(data)

    report_summary = get_report_summary(
        data,
        employment_types,
    )

    return columns, data, None, chart, report_summary


# def get_employment_types(filters):
#     """
#     Return Employment Types for dynamic report columns.

#     If the Employment Type filter is selected, only the selected
#     Employment Type column is shown. Otherwise, all Employment Types
#     are displayed.
#     """

#     if filters.get("employment_type"):
#         employment_type_names = [
#             filters.employment_type
#         ]
#     else:
#         employment_type_names = frappe.get_all(
#             "Employment Type",
#             pluck="name",
#             order_by="name asc",
#         )

#     employment_types = []

#     for index, employment_type in enumerate(
#         employment_type_names,
#         start=1,
#     ):
#         employment_types.append(
#             {
#                 "name": employment_type,
#                 "label": employment_type,
#                 "fieldname": f"employment_type_{index}",
#             }
#         )

#     # Show employees where Employment Type has not been set.
#     # This column is hidden when a specific Employment Type is filtered.
#     if not filters.get("employment_type"):
#         employment_types.append(
#             {
#                 "name": "",
#                 "label": "Employment Type Not Set",
#                 "fieldname": "employment_type_not_set",
#             }
#         )

#     return employment_types\\\



def get_employment_types(filters):
    """
    Return only Employment Types actually used by active Employee records.

    Employment Types with no active employees are excluded.
    Empty Employment Types are also excluded.
    """

    employee_filters = {
        "status": "Active",
        "employment_type": ["is", "set"],
    }

    if filters.get("branch"):
        employee_filters["branch"] = filters.branch

    if filters.get("employment_type"):
        employee_filters["employment_type"] = (
            filters.employment_type
        )

    records = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=[
            "employment_type",
            "count(name) as employee_count",
        ],
        group_by="employment_type",
        order_by="employment_type asc",
    )

    employment_types = []

    for index, record in enumerate(records, start=1):
        if not record.employment_type:
            continue

        if int(record.employee_count or 0) <= 0:
            continue

        employment_types.append(
            {
                "name": record.employment_type,
                "label": record.employment_type,
                "fieldname": f"employment_type_{index}",
            }
        )

    return employment_types


def get_columns(employment_types):
    columns = [
        {
            "label": _("Branch"),
            "fieldname": "branch",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Employee Total"),
            "fieldname": "employee_total",
            "fieldtype": "Int",
            "width": 130,
        },
    ]

    # Dynamic columns for Operator, Regular, Contract, etc.
    for employment_type in employment_types:
        columns.append(
            {
                "label": _(employment_type["label"]),
                "fieldname": employment_type["fieldname"],
                "fieldtype": "Int",
                "width": 140,
            }
        )

    # Columns for the custom employee DocTypes.
    for employee_type in OTHER_EMPLOYEE_TYPES:
        columns.append(
            {
                "label": _(employee_type["label"]),
                "fieldname": employee_type["fieldname"],
                "fieldtype": "Int",
                "width": 150,
            }
        )

    columns.append(
        {
            "label": _("Total Employees"),
            "fieldname": "total_employees",
            "fieldtype": "Int",
            "width": 140,
        }
    )

    return columns


def get_data(filters, employment_types):
    branch_data = {}

    add_standard_employees(
        filters,
        employment_types,
        branch_data,
    )

    add_other_employee_types(
        filters,
        employment_types,
        branch_data,
    )

    data = list(branch_data.values())

    # Highest employee count first.
    # Branch Not Set will appear at the bottom.
    data.sort(
        key=lambda row: (
            row["branch"] == _("Branch Not Set"),
            -row["total_employees"],
            row["branch"],
        )
    )

    return data


def add_standard_employees(
    filters,
    employment_types,
    branch_data,
):
    """
    Add active employees from the standard Employee DocType and
    group them by Branch and Employment Type.
    """

    employee_filters = {
        "status": "Active",
    }

    if filters.get("branch"):
        employee_filters["branch"] = filters.branch

    if filters.get("employment_type"):
        employee_filters["employment_type"] = (
            filters.employment_type
        )

    records = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=[
            "branch",
            "employment_type",
            "count(name) as employee_count",
        ],
        group_by="branch, employment_type",
    )

    employment_type_map = {
        employment_type["name"]: employment_type["fieldname"]
        for employment_type in employment_types
    }

    for record in records:
        branch = record.branch or _("Branch Not Set")
        employment_type = record.employment_type or ""
        employee_count = int(record.employee_count or 0)

        if branch not in branch_data:
            branch_data[branch] = create_branch_row(
                branch,
                employment_types,
            )

        branch_data[branch][
            "employee_total"
        ] += employee_count

        branch_data[branch][
            "total_employees"
        ] += employee_count

        employment_type_fieldname = (
            employment_type_map.get(employment_type)
        )

        if employment_type_fieldname:
            branch_data[branch][
                employment_type_fieldname
            ] += employee_count


def add_other_employee_types(
    filters,
    employment_types,
    branch_data,
):
    """
    Add records from Muster Roll, DFG & GFG, Foreign Labourer,
    Open Air Prisoner and Armed Force.
    """

    for employee_type in OTHER_EMPLOYEE_TYPES:
        doctype = employee_type["doctype"]
        fieldname = employee_type["fieldname"]
        active_status = employee_type["active_status"]

        validate_custom_doctype(doctype)

        record_filters = {
            "status": active_status,
        }

        if filters.get("branch"):
            record_filters["branch"] = filters.branch

        records = frappe.get_all(
            doctype,
            filters=record_filters,
            fields=[
                "branch",
                "count(name) as employee_count",
            ],
            group_by="branch",
        )

        for record in records:
            branch = record.branch or _("Branch Not Set")
            employee_count = int(
                record.employee_count or 0
            )

            if branch not in branch_data:
                branch_data[branch] = create_branch_row(
                    branch,
                    employment_types,
                )

            branch_data[branch][
                fieldname
            ] += employee_count

            branch_data[branch][
                "total_employees"
            ] += employee_count


def create_branch_row(branch, employment_types):
    """
    Create an empty row for a branch.
    """

    row = {
        "branch": branch,
        "employee_total": 0,
        "total_employees": 0,
    }

    for employment_type in employment_types:
        row[employment_type["fieldname"]] = 0

    for employee_type in OTHER_EMPLOYEE_TYPES:
        row[employee_type["fieldname"]] = 0

    return row


def validate_employee_fields():
    """
    Ensure the required fields exist in the standard Employee DocType.
    """

    required_fields = [
        "branch",
        "status",
        "employment_type",
    ]

    meta = frappe.get_meta("Employee")

    missing_fields = [
        fieldname
        for fieldname in required_fields
        if not meta.has_field(fieldname)
    ]

    if missing_fields:
        frappe.throw(
            _(
                "Employee is missing the following fields: {0}"
            ).format(
                ", ".join(missing_fields)
            )
        )


def validate_custom_doctype(doctype):
    """
    Ensure each custom employee DocType exists and contains
    the required branch and status fields.
    """

    if not frappe.db.exists("DocType", doctype):
        frappe.throw(
            _(
                "Employee DocType {0} does not exist."
            ).format(
                frappe.bold(doctype)
            )
        )

    meta = frappe.get_meta(doctype)
    missing_fields = []

    if not meta.has_field("branch"):
        missing_fields.append("branch")

    if not meta.has_field("status"):
        missing_fields.append("status")

    if missing_fields:
        frappe.throw(
            _(
                "{0} is missing the following fields: {1}"
            ).format(
                frappe.bold(doctype),
                ", ".join(missing_fields),
            )
        )


def get_chart(data):
    """
    Display total active employees branch-wise.
    """

    if not data:
        return None

    return {
        "data": {
            "labels": [
                row["branch"]
                for row in data
            ],
            "datasets": [
                {
                    "name": _("Total Employees"),
                    "values": [
                        row["total_employees"]
                        for row in data
                    ],
                }
            ],
        },
        "type": "bar",
        "height": 300,
        "colors": ["#169c46"],
        "barOptions": {
            "spaceRatio": 0.4,
        },
    }


# def get_report_summary(data, employment_types):
#     """
#     Generate summary cards for:

#     - Grand total
#     - Standard Employee total
#     - Every Employment Type, including Operator
#     - Every custom employee DocType, including DFG & GFG
#     """

#     grand_total = sum(
#         row.get("total_employees", 0)
#         for row in data
#     )

#     employee_total = sum(
#         row.get("employee_total", 0)
#         for row in data
#     )

#     summary = [
#         {
#             "value": grand_total,
#             "label": _("Total Active Employees"),
#             "datatype": "Int",
#             "indicator": "Green",
#         },
#         {
#             "value": employee_total,
#             "label": _("Employee Total"),
#             "datatype": "Int",
#             "indicator": "Blue",
#         },
#     ]

#     employment_type_indicators = [
#         "Blue",
#         "Orange",
#         "Green",
#         "Red",
#     ]

#     # Dynamic Employment Type cards, including Operator.
#     for index, employment_type in enumerate(
#         employment_types
#     ):
#         employment_type_total = sum(
#             row.get(
#                 employment_type["fieldname"],
#                 0,
#             )
#             for row in data
#         )

#         summary.append(
#             {
#                 "value": employment_type_total,
#                 "label": _(
#                     employment_type["label"]
#                 ),
#                 "datatype": "Int",
#                 "indicator": (
#                     employment_type_indicators[
#                         index
#                         % len(
#                             employment_type_indicators
#                         )
#                     ]
#                 ),
#             }
#         )

#     custom_type_indicators = [
#         "Orange",
#         "Blue",
#         "Red",
#         "Green",
#     ]

#     # Cards for custom employee DocTypes.
#     for index, employee_type in enumerate(
#         OTHER_EMPLOYEE_TYPES
#     ):
#         employee_type_total = sum(
#             row.get(
#                 employee_type["fieldname"],
#                 0,
#             )
#             for row in data
#         )

#         summary.append(
#             {
#                 "value": employee_type_total,
#                 "label": _(
#                     employee_type["label"]
#                 ),
#                 "datatype": "Int",
#                 "indicator": (
#                     custom_type_indicators[
#                         index
#                         % len(
#                             custom_type_indicators
#                         )
#                     ]
#                 ),
#             }
#         )

#     return summary



def get_report_summary(data, employment_types):
    """
    Summary order:

    1. Overall workforce total
    2. Employee total and Employment Type breakdown
    3. Other Employees total and custom DocType breakdown
    """

    employee_total = sum(
        row.get("employee_total", 0)
        for row in data
    )

    other_employees_total = sum(
        sum(
            row.get(employee_type["fieldname"], 0)
            for row in data
        )
        for employee_type in OTHER_EMPLOYEE_TYPES
    )

    grand_total = employee_total + other_employees_total

    summary = [
        {
            "value": grand_total,
            "label": _("Total Active Employees"),
            "datatype": "Int",
            "indicator": "Green",
        },
        {
            "value": employee_total,
            "label": _("EMPLOYEE TOTAL"),
            "datatype": "Int",
            "indicator": "Blue",
        },
    ]

    employee_indicators = [
        "Blue",
        "Green",
        "Orange",
        "Red",
    ]

    # EMPLOYEE section:
    # Employment Types from the Employee DocType only.
    for index, employment_type in enumerate(
        employment_types
    ):
        employment_type_total = sum(
            row.get(
                employment_type["fieldname"],
                0,
            )
            for row in data
        )

        summary.append(
            {
                "value": employment_type_total,
                "label": _(
                    employment_type["label"]
                ),
                "datatype": "Int",
                "indicator": employee_indicators[
                    index % len(employee_indicators)
                ],
            }
        )

    # Beginning of the OTHER EMPLOYEES section.
    summary.append(
        {
            "value": other_employees_total,
            "label": _("OTHER EMPLOYEES TOTAL"),
            "datatype": "Int",
            "indicator": "Orange",
        }
    )

    other_indicators = [
        "Orange",
        "Blue",
        "Red",
        "Green",
    ]

    # OTHER EMPLOYEES section:
    # Counts from the separate custom DocTypes.
    for index, employee_type in enumerate(
        OTHER_EMPLOYEE_TYPES
    ):
        category_total = sum(
            row.get(
                employee_type["fieldname"],
                0,
            )
            for row in data
        )

        summary.append(
            {
                "value": category_total,
                "label": _(
                    employee_type["label"]
                ),
                "datatype": "Int",
                "indicator": other_indicators[
                    index % len(other_indicators)
                ],
            }
        )

    return summary