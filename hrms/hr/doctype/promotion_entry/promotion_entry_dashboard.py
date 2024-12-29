from frappe import _

def get_data():
	return {
		"fieldname": "promotion_entry",
		"non_standard_fieldnames": {},
		"transactions": [
			{"label": _("Transactions"), "items": ["Employee Promotion"]},
		]
	}
