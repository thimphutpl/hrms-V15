frappe.listview_settings["Muster Roll Attendance"] = {
    add_fields: ["status", "attendance_date"],

    get_indicator: function (doc) {
		if (["Present"].includes(doc.status)) {
			return [__(doc.status), "green", "status,=," + doc.status];
		} else if (["Absent"].includes(doc.status)) {
			return [__(doc.status), "red", "status,=," + doc.status];
		} else if (doc.status == "Half Day") {
			return [__(doc.status), "orange", "status,=," + doc.status];
		}
	},
}