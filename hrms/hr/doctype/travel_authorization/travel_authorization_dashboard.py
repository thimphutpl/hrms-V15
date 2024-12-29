from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'ta',
        # "non_standard_fieldnames": {"Project Payment": "reference_name"},
		'transactions': [
			{
				'label': _('Related'),
				'items': ['Travel Claim']
			}
        ]
	}
