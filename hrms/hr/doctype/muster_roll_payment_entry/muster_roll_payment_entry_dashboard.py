def get_data():
	return {
		"fieldname": "muster_roll_payment_entry",
		"non_standard_fieldnames": {
			"Journal Entry": "reference_name",
			"Payment Entry": "reference_name",
		},
		"transactions": [{"items": ["Pay Slip", "Journal Entry"]}],
	}
