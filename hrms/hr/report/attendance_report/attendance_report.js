// frappe.query_reports["Attendance Report"] = {
// 	"filters": [
	
// 		{
// 			fieldname: "from_date",
// 			label: __("From Date"),
// 			fieldtype: "Date",
// 			reqd: 1,
// 			default: frappe.datetime.month_start()
// 		},
// 		{
// 			fieldname: "to_date",
// 			label: __("To Date"),
// 			fieldtype: "Date",
// 			reqd: 1,
// 			default: frappe.datetime.month_end()
// 		}
// 	],

// 	formatter: function (value, row, column, data, default_formatter) {

// 		value = default_formatter(value, row, column, data);

// 		if (!data) {
// 			return value;
// 		}

// 		// Skip Employee Columns
// 		if (["employee", "employee_name"].includes(column.fieldname)) {
// 			return value;
// 		}

// 		// Holiday
// 		if (data[column.fieldname] === "H") {
// 			value = `<span style="
// 				background:gray;
// 				color:white;
// 				padding:2px 8px;
// 				border-radius:6px;
// 				font-weight:bold;
// 			">H</span>`;
// 		}

// 		// Leave
// 		else if (data[column.fieldname] === "L") {
// 			value = `<span style="
// 				background:#166534;
// 				color:white;
// 				padding:2px 8px;
// 				border-radius:6px;
// 				font-weight:bold;
// 			">L</span>`;
// 		}

// 		// Half Day
// 		else if (data[column.fieldname] === "HD") {
// 			value = `<span style="
// 				background:orange;
// 				color:white;
// 				padding:2px 8px;
// 				border-radius:6px;
// 				font-weight:bold;
// 			">HD</span>`;
// 		}

// 		// Tour
// 		else if (data[column.fieldname] === "Tour") {
// 			value = `<span style="
// 				background:blue;
// 				color:white;
// 				padding:2px 8px;
// 				border-radius:6px;
// 				font-weight:bold;
// 			">T</span>`;
// 		}

// 		// Absent
// 		else if (data[column.fieldname] === "A") {
// 			value = `<span style="
// 				background:#7f1d1d;
// 				color:white;
// 				padding:2px 8px;
// 				border-radius:6px;
// 				font-weight:bold;
// 			">A</span>`;
// 		}

// 		// Shift / Present
// 		else {
// 			value = `<span style="
// 				background:white;
// 				color:black;
// 				padding:2px 8px;
// 				border-radius:6px;
// 				font-weight:bold;
// 			">${data[column.fieldname]}</span>`;
// 		}

// 		return value;
// 	}
// };

frappe.query_reports["Attendance Report"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_start()
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.month_end()
		}
	],

	// formatter: function (value, row, column, data, default_formatter) {

	// 	value = default_formatter(value, row, column, data);

	// 	if (!data) {
	// 		return value;
	// 	}

	// 	// Skip Employee Columns
	// 	if (["employee", "employee_name"].includes(column.fieldname)) {
	// 		return value;
	// 	}

	// 	const val = data[column.fieldname];

	// 	// Holiday
	// 	if (val === "H") {
	// 		value = `<span style="
	// 			background: gray;
	// 			color: white;
	// 			padding: 2px 8px;
	// 			border-radius: 6px;
	// 			font-weight: bold;
	// 		">H</span>`;
	// 	}

	// 	// Leave
	// 	else if (val === "L") {
	// 		value = `<span style="
	// 			background: #166534;
	// 			color: white;
	// 			padding: 2px 8px;
	// 			border-radius: 6px;
	// 			font-weight: bold;
	// 		">L</span>`;
	// 	}

	// 	// Half Day
	// 	else if (val === "HD") {
	// 		value = `<span style="
	// 			background: orange;
	// 			color: white;
	// 			padding: 2px 8px;
	// 			border-radius: 6px;
	// 			font-weight: bold;
	// 		">HD</span>`;
	// 	}

	// 	// Tour
	// 	else if (val === "T") {
	// 		value = `<span style="
	// 			background: blue;
	// 			color: white;
	// 			padding: 2px 8px;
	// 			border-radius: 6px;
	// 			font-weight: bold;
	// 		">T</span>`;
	// 	}

	// 	// Absent
	// 	else if (val === "A") {
	// 		value = `<span style="
	// 			background: #7f1d1d;
	// 			color: white;
	// 			padding: 2px 8px;
	// 			border-radius: 6px;
	// 			font-weight: bold;
	// 		">A</span>`;
	// 	}

	// 	// Present / Shift or default
	// 	else {
	// 		value = `<span style="
	// 			background: white;
	// 			color: black;
	// 			padding: 2px 8px;
	// 			border-radius: 6px;
	// 			font-weight: bold;
	// 		">${val}</span>`;
	// 	}

	// 	return value;
	// }
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		const summarized_view = frappe.query_report.get_filter_value("summarized_view");
		const group_by = frappe.query_report.get_filter_value("group_by");

		if (group_by && column.colIndex === 1) {
			value = "<strong>" + value + "</strong>";
		}

		if (!summarized_view) {
			if ((group_by && column.colIndex > 3) || (!group_by && column.colIndex > 2)) {
				if (value == "P" || value == "WFH")
					value = "<span style='color:green'>" + value + "</span>";
				else if (value == "A") value = "<span style='color:red'>" + value + "</span>";
				else if (value == "HD") value = "<span style='color:orange'>" + value + "</span>";
				else if (value == "L") value = "<span style='color:#318AD8'>" + value + "</span>";
				else if (value == "T") value = "<span style='color:blue'>" + value + "</span>";
			}
		}

		return value;
	},
	
};