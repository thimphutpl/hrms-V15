// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["PBVA Report"] = {
	
	"filters": [
	
		{		
			"fieldname":"branch",
			"label": ("Branch"),
			"fieldtype": "Link",
			"options": "Branch",
			"width": "100"
		},

		{
			"fieldname":"fiscal_year",
			"label": ("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"width": "100"
		},

	]
};
