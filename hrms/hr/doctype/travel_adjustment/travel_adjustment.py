# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from datetime import timedelta
from frappe.utils import (
    add_days,
    ceil,
    cint,
    cstr,
    date_diff,
    floor,
    flt,
    formatdate,
    get_first_day,
    get_last_day,
    get_link_to_form,
    getdate,
    money_in_words,
    rounded,
    nowdate,
)
from frappe.model.mapper import get_mapped_doc
from hrms.hr.utils import validate_active_employee
from erpnext.custom_workflow import validate_workflow_states, notify_workflow_states


class TravelAdjustment(Document):
    def validate(self):
        """Validate the document before saving."""
        validate_active_employee(self.employee)
        self._validate_travel_last_day()
        validate_workflow_states(self)

    def on_update(self):
        """Check for date overlaps when the document is updated."""
        self._check_date_overlap()

    def on_submit(self):
        """Update the linked Travel Authorization when the document is submitted."""
        self.create_attendance()
        self._update_travel_authorization()

    def on_cancel(self):
        """Update the linked Travel Authorization when the document is canceled."""
        self._update_travel_authorization(cancel=True)
        self.cancel_attendance()

    def _validate_travel_last_day(self):
        """Ensure only the last item in the itinerary is marked as the last day."""
        if self.get("items"):
            for item in self.items:
                item.is_last_day = 0
            self.items[-1].is_last_day = 1

    def create_attendance(self):
        for row in self.items:
            from_date = getdate(row.from_date)
            to_date = getdate(row.to_date) if cint(row.halt) else getdate(row.from_date)
            noof_days = date_diff(to_date, from_date) + 1
            for a in range(noof_days):
                attendance_date = from_date + timedelta(days=a)
                al = frappe.db.sql(
                    """select name from tabAttendance 
						where docstatus = 1 and employee = %s 
						and attendance_date = %s""",
                    (self.employee, str(attendance_date)),
                    as_dict=True,
                )
                if al:
                    doc = frappe.get_doc("Attendance", al[0].name)
                    doc.cancel()

                # create attendance
                attendance = frappe.new_doc("Attendance")
                attendance.flags.ignore_permissions = 1
                attendance.employee = self.employee
                attendance.employee_name = self.employee_name
                attendance.attendance_date = attendance_date
                attendance.status = "Tour"
                attendance.branch = self.branch
                attendance.company = frappe.db.get_value(
                    "Employee", self.employee, "company"
                )
                attendance.reference_name = self.travel_authorization
                attendance.submit()

    def cancel_attendance(self):
        if frappe.db.exists(
            "Attendance", {"reference_name": self.travel_authorization}
        ):
            frappe.db.sql(
                "delete from tabAttendance where reference_name = %s",
                (self.travel_authorization),
            )

    def _check_date_overlap(self):
        """Check for overlapping dates in the itinerary items."""
        overlap_query = """
			SELECT t1.idx, t2.idx AS overlap_idx
			FROM `tabTravel Adjustment Item` t1
			JOIN `tabTravel Adjustment Item` t2
			ON t1.parent = t2.parent
			AND t1.name != t2.name
			AND t1.from_date <= t2.to_date
			AND t1.to_date >= t2.from_date
			WHERE t1.parent = %s
		"""
        overlaps = frappe.db.sql(overlap_query, (self.name,), as_dict=True)

        if overlaps:
            first_overlap = overlaps[0]
            frappe.throw(
                _("Row#{}: Dates are overlapping with dates in Row#{}").format(
                    first_overlap["idx"], first_overlap["overlap_idx"]
                )
            )

    def _update_travel_authorization(self, cancel=False):
        """
        Update the linked Travel Authorization by deleting and re-inserting items.
        If `cancel` is True, use `itinerary`; otherwise, use `items`.
        """
        try:
            # Delete existing Travel Authorization Items
            frappe.db.sql(
                "DELETE FROM `tabTravel Authorization Item` WHERE parent = %s",
                (self.travel_authorization,),
            )

            # Determine which items to insert based on the `cancel` flag
            items_to_insert = self.itinerary if cancel else self.items

            # Insert new Travel Authorization Items
            self._insert_travel_authorization_items(items_to_insert)

            # Commit the transaction
            frappe.db.commit()

        except Exception as e:
            # Rollback in case of any error
            frappe.db.rollback()
            frappe.log_error(f"Error updating Travel Authorization: {e}")
            raise e

    def _insert_travel_authorization_items(self, items):
        """Helper method to insert Travel Authorization Items."""
        for item in items:
            frappe.get_doc(
                {
                    "doctype": "Travel Authorization Item",
                    "parenttype": "Travel Authorization",
                    "parentfield": "items",
                    "idx": item.idx,
                    "parent": self.travel_authorization,
                    "from_date": item.from_date,
                    "to_date": item.to_date,
                    "halt": item.halt,
                    "halt_at": item.halt_at,
                    "travel_from": item.travel_from,
                    "travel_to": item.travel_to,
                    "is_last_day": item.is_last_day,
                }
            ).insert(ignore_permissions=True)


@frappe.whitelist()
def make_travel_adjustment(source_name, target_doc=None):
    """
    Create a Travel Adjustment document from a Travel Authorization.
    """

    # frappe.throw(str(source_name))
    def set_missing_values(source, target):
        """Copy itinerary items from the source Travel Authorization to the target Travel Adjustment."""
        for item in source.get("items"):
            target.append("itinerary", item.as_dict())

    doclist = get_mapped_doc(
        "Travel Authorization",
        source_name,
        {
            "Travel Authorization": {
                "doctype": "Travel Adjustment",
                "field_map": {"name": "travel_authorization", 
                              "employee": "employee",
                              "approver":"approver",
                              "approver_name":"approver_name",
                              "approver_designation":"approver_designation",
                              "reports_to":"reports_to",
                              "reports_to_name":"reports_to_name"
                              },
                "validation": {
                    "docstatus": ["=", 1],
                },
            },
            "Travel Authorization Item": {
                "doctype": "Travel Adjustment Item",
                "field_map": {
                    "from_date": "from_date",
                    "travel_from": "travel_from",
                    "to_date": "to_date",
                    "travel_to": "travel_to",
                },
            },
        },
        target_doc,
        set_missing_values,
    )

    return doclist


def get_permission_query_conditions(user):
    if not user:
        user = frappe.session.user

    user_roles = frappe.get_roles(user)
    
    if user == "Administrator":
        return
    
    # Base conditions: owner, employee link, and approver view
    conditions = f"""
		(
			`tabTravel Adjustment`.owner = '{user}'
			OR
			EXISTS (
				SELECT 1 FROM `tabEmployee`
				WHERE `tabEmployee`.name = `tabTravel Adjustment`.employee
				AND `tabEmployee`.user_id = '{user}'
				AND `tabTravel Adjustment`.docstatus != 2
			)
			OR
			(`tabTravel Adjustment`.approver = '{user}'
			 AND `tabTravel Adjustment`.workflow_state NOT IN ('Draft', 'Rejected', 'Cancelled', 'Waiting for Verification'))
	"""
    if "Verifier" in user_roles:
        conditions += f"""
			OR
			(`tabTravel Adjustment`.reports_to = '{user}'
			 AND `tabTravel Adjustment`.workflow_state = 'Waiting for Verification')
		"""
    conditions += ")"

    return conditions

    
