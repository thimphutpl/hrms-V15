# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SemsoAllocatedAmount(Document):
	pass

class SemsoAllocatedAmount(Document):
    pass

@frappe.whitelist()
def get_all_semso(company, branch, fiscal_year, month):
  
    if not company:
        frappe.throw("Company is required")
    

    filters = {
        "company": company,
    }
    
    if branch:
        filters["branch"] = branch
        
    if fiscal_year:
        filters["fiscal_year"] = fiscal_year
    if month:
        filters["month"] = month
    
    # Get all Semso Entry records
    semso_entries = frappe.get_all(
        "Semso Entry",
        filters=filters,
        fields=["company", "branch", "fiscal_year", "month"]
    )
    
    # For each entry, get the contribution details
    result = []
    for entry in semso_entries:
        # Get child table data
        contributions = frappe.get_all(
            "Semso Contribution Item",
            filters={"parent": entry.name},
            fields=["employee", "name1", "grade", "amount"]
        )
        
        # Add contributions to the entry
        entry["contributions"] = contributions
        result.append(entry)
    
    return result