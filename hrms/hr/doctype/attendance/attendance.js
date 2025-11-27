// // Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and Contributors
// // License: GNU General Public License v3. See license.txt

// frappe.ui.form.on("Attendance", {
// 	refresh(frm) {
// 		if (frm.doc.__islocal && !frm.doc.attendance_date) {
// 			frm.set_value("attendance_date", frappe.datetime.get_today());
// 		}

// 		frm.set_query("employee", () => {
// 			return {
// 				query: "erpnext.controllers.queries.employee_query",
// 			};
// 		});
// 	},
// });


frappe.ui.form.on("Attendance", {
	refresh(frm) {
		if (frm.doc.__islocal && !frm.doc.attendance_date) {
			frm.set_value("attendance_date", frappe.datetime.get_today());
		}

		frm.set_query("employee", () => {
			return {
				query: "erpnext.controllers.queries.employee_query",
			};
		});

		frappe.db.get_single_value("HR Settings", "allow_geolocation_tracking")
			.then((allow) => {
				if (!allow) {
					frm.set_df_property("in_latitude", "hidden", 1);
					frm.set_df_property("in_longitude", "hidden", 1);
					frm.set_df_property("geolocation", "hidden", 1);
				} else {
					frm.set_df_property("geolocation", "hidden", 0);
					frm.set_df_property("geolocation", "read_only", 1);

					// Populate geolocation from latitude/longitude
					update_geolocation(frm);
				}
			});
	},

	in_latitude(frm) {
		update_geolocation(frm);
	},
	in_longitude(frm) {
		update_geolocation(frm);
	},
});

// Function to update the geolocation field
function update_geolocation(frm) {
	const lat = frm.doc.in_latitude;
	const long = frm.doc.in_longitude;

	if (lat && long) {
		// Set the value for the Geolocation field
		frm.set_value("geolocation", `${lat}, ${long}`);

		// Optional: trigger refresh so the map renders
		frm.refresh_field("geolocation");
	}
}
