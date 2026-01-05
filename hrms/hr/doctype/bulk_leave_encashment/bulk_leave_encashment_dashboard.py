def get_data():
	return {
		"fieldname": "bulk_leave_encashment",
		"non_standard_fieldnames": {
			"Journal Entry": "reference_name",
		},
		"transactions": [{"items": ["Journal Entry"]}],
	}
