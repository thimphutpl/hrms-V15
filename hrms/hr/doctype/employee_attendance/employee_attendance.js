
frappe.ui.form.on('Employee Attendance', {

    refresh: async (frm) => {
        const allow_geolocation_tracking = await frappe.db.get_single_value(
            "HR Settings",
            "allow_geolocation_tracking",
        );

        if (!allow_geolocation_tracking) {
            hide_field(["fetch_geolocation", "latitude", "longitude", "geolocation"]);
            return;
        }
        if (!frm.is_new()) {
            lock_fields(frm);
        }
        handle_log_type(frm);

    },
    on_submit(frm) {
        lock_fields(frm);
    },
    log_type: function (frm) {
        handle_log_type(frm);
    },

    setup: function (frm) {
        // Filter Shift dropdown based on branch, active, date, and fiscal year
        frm.set_query("shift", function () {
            if (!frm.doc.time) return { filters: { is_active: 1 } }; // fallback

            let attendance_date = frappe.datetime.get_datetime_as_string(frm.doc.time).split(" ")[0];
            let day_of_week = frappe.datetime.str_to_obj(frm.doc.time).getDay()
            let weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
            let current_day = weekdays[day_of_week];



            return {
                filters: [
                    ["Attendance Shift", "is_active", "=", 1],
                    ["Attendance Shift", "attendance_branch", "=", frm.doc.attendance_branch],
                    ["Attendance Shift", "valid_from", "<=", attendance_date],
                    ["Attendance Shift", "valid_to", ">=", attendance_date],
                    ["Attendance Shift", "day", "=", current_day]
                ]
            };
        });
    },

    attendance_branch: function (frm) {
        frm.set_value("shift", null);
        frm.refresh_field("shift");

    },
    after_save: function (frm) {
        frappe.set_route("List", "Employee Attendance");
    },
    fetch_geolocation: (frm) => {
        hrms.fetch_geolocation(frm);
    },
});




function lock_fields(frm) {
    frm.set_df_property("log_type", "read_only", 1);
    frm.set_df_property("time", "read_only", 1);
    frm.set_df_property("employee", "read_only", 1);
    frm.set_df_property("fetch_geolocation", "hidden", 1);
    frm.set_df_property("late_reason", "read_only", 1);
    frm.set_df_property("early_exit_reason", "read_only", 1);
}

function handle_log_type(frm) {
    const log_type = frm.doc.log_type;

    if (log_type === "IN") {
        frm.set_df_property('late_reason', 'hidden', 0);          // show late_reason
        frm.set_df_property('early_exit_reason', 'hidden', 1);    // hide early_exit_reason
    } else if (log_type === "OUT") {
        frm.set_df_property('late_reason', 'hidden', 1);          // hide late_reason
        frm.set_df_property('early_exit_reason', 'hidden', 0);    // show early_exit_reason
    } else {
        frm.set_df_property('late_reason', 'hidden', 1);
        frm.set_df_property('early_exit_reason', 'hidden', 1);
    }
}