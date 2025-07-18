def get_data():
	return {
		"fieldname": "bulk_travel_authorization",
		"non_standard_fieldnames": {
			"Payment Entry": "reference_name",
			"Journal Entry": "reference_name",
		},
		"transactions": [{"items": ["Payment Entry", "Journal Entry"]}],
	}
