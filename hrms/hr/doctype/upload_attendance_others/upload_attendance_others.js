// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.provide("hrms.hr");

hrms.hr.MRAttendanceControlPanel = class AttendanceControlPanel extends frappe.ui.form.Controller {
	onload() {
	}

	refresh() {
		this.frm.disable_save();
		this.show_upload();
		this.setup_import_progress();
	}

	get_template () {
		if(!this.frm.doc.fiscal_year || !this.frm.doc.month || !this.frm.doc.branch) {
			msgprint(__("Fiscal Year, Month, and branch are mandatory"));
			return;
		}
		window.location.href = repl(frappe.request.url +
			'?cmd=%(cmd)s&fiscal_year=%(fiscal_year)s&month=%(month)s&branch=%(branch)s', {
				cmd: "hrms.hr.doctype.upload_attendance_others.upload_attendance_others.get_template",
				branch: this.frm.doc.branch,
				fiscal_year: this.frm.doc.fiscal_year,
				month: this.frm.doc.month,
			});
	}

	show_upload() {
		let $wrapper = $(this.frm.fields_dict.upload_html.wrapper).empty();
		new frappe.ui.FileUploader({
			wrapper: $wrapper,
			method: "hrms.hr.doctype.upload_attendance_others.upload_attendance_others.upload",
		});
		$wrapper.addClass("pb-5");
	}

	setup_import_progress() {
		var $log_wrapper = $(this.frm.fields_dict.import_log.wrapper).empty();

		frappe.realtime.on("import_attendance", (data) => {
			if (data.progress) {
				this.frm.dashboard.show_progress(
					"Import Attendance",
					(data.progress / data.total) * 100,
					__("Importing {0} of {1}", [data.progress, data.total]),
				);
				if (data.progress === data.total) {
					this.frm.dashboard.hide_progress("Import Attendance");
				}
			} else if (data.error) {
				this.frm.dashboard.hide();
				let messages = [`<th>${__("Error in some rows")}</th>`]
					.concat(
						data.messages
							.filter((message) => message.includes("Error"))
							.map((message) => `<tr><td>${message}</td></tr>`),
					)
					.join("");
				$log_wrapper.append('<table class="table table-bordered">' + messages);
			} else if (data.messages) {
				this.frm.dashboard.hide();
				let messages = [`<th>${__("Import Successful")}</th>`]
					.concat(data.messages.map((message) => `<tr><td>${message}</td></tr>`))
					.join("");
				$log_wrapper.append('<table class="table table-bordered">' + messages);
			}
		});
	}
    
	// show_upload() {
	// 	var me = this;
	// 	var $wrapper = $(cur_frm.fields_dict.upload_html.wrapper).empty();

	// 	// upload
	// 	frappe.upload.make({
	// 		parent: $wrapper,
	// 		args: {
	// 			method: 'hrms.hr.doctype.upload_attendance_others.upload_attendance_others.upload'
	// 		},
	// 		sample_url: "e.g. http://example.com/somefile.csv",
	// 		callback: function(attachment, r) {
	// 			var $log_wrapper = $(cur_frm.fields_dict.import_log.wrapper).empty();

	// 			if(!r.messages) r.messages = [];
	// 			// replace links if error has occured
	// 			if(r.exc || r.error) {
	// 				r.messages = $.map(r.message.messages, function(v) {
	// 					var msg = v.replace("Inserted", "Valid")
	// 						.replace("Updated", "Valid").split("<");
	// 					if (msg.length > 1) {
	// 						v = msg[0] + (msg[1].split(">").slice(-1)[0]);
	// 					} else {
	// 						v = msg[0];
	// 					}
	// 					return v;
	// 				});

	// 				r.messages = ["<h4 style='color:red'>"+__("Import Failed!")+"</h4>"]
	// 					.concat(r.messages)
	// 			} else {
	// 				r.messages = ["<h4 style='color:green'>"+__("Import Successful!")+"</h4>"].
	// 					concat(r.message.messages)
	// 			}

	// 			$.each(r.messages, function(i, v) {
	// 				var $p = $('<p>').html(v).appendTo($log_wrapper);
	// 				if(v.substr(0,5)=='Error') {
	// 					$p.css('color', 'red');
	// 				} else if(v.substr(0,8)=='Inserted') {
	// 					$p.css('color', 'green');
	// 				} else if(v.substr(0,7)=='Updated') {
	// 					$p.css('color', 'green');
	// 				} else if(v.substr(0,5)=='Valid') {
	// 					$p.css('color', '#777');
	// 				}
	// 			});
	// 		}
	// 	});

	// 	// rename button
	// 	$wrapper.find('form input[type="submit"]')
	// 		.attr('value', 'Upload and Import')
	// }
};

cur_frm.cscript = new hrms.hr.MRAttendanceControlPanel({frm: cur_frm});
