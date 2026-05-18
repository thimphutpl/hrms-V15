frappe.ui.form.on('Upload Attendance Others', {
    refresh: function(frm) {
    // frm.set_query("section", function() {
            //      return {
            //              "filters": {
            //                      "disabled":0,
            //                      "is_section":1
            //              }
            //      };
            // });
		frm.set_query("unit", function() {
			return {
				"filters": {
					"disabled":0,
					"is_unit":1,
				}
			};
		});
    },
upload_data:function(frm){
    frappe.call({
        method:"upload_data",
        doc:frm.doc,
        callback:function(r){

        },
        freeze: true,
                    freeze_message: '<span style="color:white; background-color: red; padding: 10px 50px; border-radius: 5px;">Uploading Data.....</span>'
    })
},
    get_template:function(frm) {
            if(!frm.doc.fiscal_year || !frm.doc.month || !frm.doc.branch || !frm.doc.file_type || !frm.doc.upload_type) {
                    msgprint(__("Fiscal Year, Month, Branch and File Type are mandatory"));
                    return;
            }
            var unitValue = frm.doc.unit ? frm.doc.unit : 1;
            console.log(unitValue)
    open_url_post(
        '/api/method/hrms.hr.doctype.upload_attendance_others.upload_attendance_others.download_template',
        {
            file_type: frm.doc.file_type,
            branch : frm.doc.branch,
            month: frm.doc.month,
            fiscal_year: frm.doc.fiscal_year,
            upload_type: frm.doc.upload_type,
            unit: unitValue
        }
    )
    },
});