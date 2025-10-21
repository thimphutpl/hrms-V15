frappe.pages['daily-attendance'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: '',
        single_column: true
    });

    
    

    
    const button_html = `
        <div class="container text-center">
            <div class="row">
                <div class="col">
                    <button class="btn btn-success" id="sign-in" style="display: none;">
                        sign in
                    </button>
                    <button class="btn btn-success" id="sign-out" style="display: none;">
                        sign out
                    </button>
                </div>
              </div>
              <br>
                 <div class="row">
                 <div class="col">
                    <b>Sign In:<p id="sign-in-time"> </p></b>
                 </div>
               </div>
               <div class="row">
                 <div class="col">
                <b> Sign Out:<p id="sign-out-time"></p></b>
                 </div>
               </div>
        </div>`;

    
    $(button_html).appendTo(page.main);

    
    // frappe.call('hrms.hr.hr_custom_function.is_ip_authorized').then(response => {
	// 	if (response.message) {
            
	// 		$('#sign-in').show();
	// 		$('#sign-out').show();
    //         load_todays_attendance();
	// 	} else {

            fetch('https://api.ipify.org?format=json')
            .then(response => response.json())
            .then(data => {
                const clientIp = data.ip;
                //alert('Your IP is: ' + clientIp);

                    frappe.call({
                    method: 'hrms.hr.page.daily_attendance.daily_attendance.is_ip_authorized',
                    args: {
                        'ip_address': clientIp
                    },
                    callback: function(response) {
                        if (response.message) {
                            
                            $('#sign-in').show();
                            $('#sign-out').show();
                            load_todays_attendance();
                            
                        } else {
                            
                            frappe.show_alert({
                                message: __('Your IP ' + clientIp + ' is not authorized'),
                                indicator: 'red'
                            });
                        }
                    }
                });
                
            });
            
	// 		frappe.msgprint("Access denied: Your IP is not authorized.");
	// 	}
	// });

    
    $('#sign-in').on('click', function() {
    frappe.call({
        method: "hrms.hr.page.daily_attendance.daily_attendance.sign_in",  // Adjust method path
        callback: function(response) {
            if (response.message) {
                frappe.msgprint(__("Signed in successfully. Attendance: {0}", [response.message.attendance]));
                console.log("Success:", response.message);
            }
        },
        error: function(err) {
            console.error("Error:", err);
            frappe.msgprint(__("Sign-in failed. Please try again."));
        }
    });
});

$('#sign-out').on('click', function() {
    frappe.call({
        method: "hrms.hr.page.daily_attendance.daily_attendance.sign_out",  // Adjust method path
        callback: function(response) {
            if (response.message) {
                frappe.msgprint(__("Signed out successfully. Attendance: {0}", [response.message.attendance]));
                console.log("Success:", response.message);
            }
        },
        error: function(err) {
            console.error("Error:", err);
            frappe.msgprint(__("Sign-out failed. Please try again."));
        }
    });
});
};

function load_todays_attendance() {
    
    frappe.call({
        method: "hrms.hr.page.daily_attendance.daily_attendance.get_todays_attendance",
        callback: function(response) {
            if (response.message) {
                if (response.message.sign_in_time) {
                    $('#sign-in-time').text(response.message.sign_in_time);
                }
                if (response.message.sign_out_time) {
                    $('#sign-out-time').text(response.message.sign_out_time);
                }
            }
        }
    });
}
