// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("test", {
            setup: function (frm) {
		     frm.set_query("employee", function () {
			    return {
				filters: {
					status: "Active",
                        },
                    };
                });
            },
            refresh(frm) {
               
            },
            employee: function (frm) {
                if (frm.doc.employee) 
                    {
                        frm.trigger("get_client_ip")

                    }
		
	        },

            get_client_ip:function(frm){

                frappe.call({
                        method: "hrms.hr.hr_custom_function.get_client_ip_api",
                        callback: function(response) {
                            if (response.message) {
                                //if(response.message.client_ip=="119.2.118.128"){
                                    frappe.msgprint("Your IP: " + response.message.client_ip);
                                    frm.set_value('sign_ip',response.message.client_ip);
                                    //frm.set_value('sigin_time',frappe.datetime.now_time());
                                    //frm.set_df_property('sign_ip', 'hidden', 0);
                                // }
                                // else{
                                //     frappe.msgprint("hi")
                                //     frm.set_df_property('sign_ip', 'hidden', 1);
                                // }
                            }
                        },
                        error: function(err) {
                            frappe.msgprint("Failed to fetch IP: " + err);
                        }
                    });


            }


 });
