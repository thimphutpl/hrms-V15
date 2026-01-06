// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Checkin", {

	refresh: async (frm) => {
		if (!frm.doc.__islocal) frm.trigger("add_fetch_shift_button");

		const allow_geolocation_tracking = await frappe.db.get_single_value(
			"HR Settings",
			"allow_geolocation_tracking",
		);

		if (!allow_geolocation_tracking) {
			hide_field(["fetch_geolocation", "latitude", "longitude", "geolocation"]);
			return;
		}
		if (!frappe.user.has_role(["HR User", "HR Manager", "Administrator"])) {

			frm.set_df_property("device_id", "hidden", 1);
			frm.set_df_property("skip_auto_attendance", "hidden", 1);
		}
		if (!frm.is_new()) {
			lock_fields(frm);
		}
	},
	on_submit(frm) {
		lock_fields(frm);
	},

	onload_post_render(frm) {
		if (!frm.is_new()) {
			lock_fields(frm);
		}
	},
	after_save: function (frm) {
		frappe.set_route("List", "Employee Checkin");
	},
	fetch_geolocation: (frm) => {
		hrms.fetch_geolocation(frm);
	},

	add_fetch_shift_button(frm) {
		if (frm.doc.attendace) return;
		frm.add_custom_button(__("Fetch Shift"), function () {
			const previous_shift = frm.doc.shift;
			frappe.call({
				method: "fetch_shift",
				doc: frm.doc,
				freeze: true,
				freeze_message: __("Fetching Shift"),
				callback: function () {
					if (previous_shift === frm.doc.shift) return;
					frm.dirty();
					frm.save();
					frappe.show_alert({
						message: __("Shift has been successfully updated to {0}.", [
							frm.doc.shift,
						]),
						indicator: "green",
					});
				},
			});
		});
	},
});
function lock_fields(frm) {
	frm.set_df_property("log_type", "read_only", 1);
	frm.set_df_property("time", "read_only", 1);
	frm.set_df_property("employee", "read_only", 1);
	frm.set_df_property("fetch_geolocation", "hidden", 1);
}