cur_frm.add_fetch("employee", "employee_name", "employee_name")

frappe.ui.form.on('SWS Application', {
        refresh: function(frm) {
                if(!frm.doc.posting_date) {
                        frm.set_value("posting_date", get_today())
                }
        }
});
frappe.ui.form.on('SWS Application Item', {
        sws_event: function(frm, cdt, cdn) {
                var row = locals[cdt][cdn];
                if(!row.reference_document){
                        frappe.throw("Please select reference document first.")
                }
                if(row.sws_event == "" || row.sws_event == null){
                        frappe.model.set_value(cdt, cdn, "claim_amount",null);
                        frm.model.set_value(cdt, cdn, "amount", null);
                }
                frappe.call({
                        method: "erpnext.hr.doctype.sws_application.sws_application.get_event_amount",
                        args: {"sws_event":row.sws_event, "reference":row.reference_document, "employee":frm.doc.employee},
                        callback: function(r){
                                if(r.message){
                                        console.log(r.message)
                                        frappe.model.set_value(cdt, cdn, "claim_amount", r.message[0]['amount']);
                                        frappe.model.set_value(cdt, cdn, "amount", r.message[0]['amount']);
                                        frm.refresh_field("claim_amount");
                                        frm.refresh_field("amount");
                                }
                        }
                })
        },
});

cur_frm.fields_dict['items'].grid.get_field('reference_document').get_query = function(frm, cdt, cdn) {
        if (!frm.employee) {
                frm.employee = "dhskhfgskhfgsfhksfsjhbaf"
        }
        return {
                query : "erpnext.controllers.queries.filter_sws_member_item",
                filters: {
                        "employee": frm.employee,
                        "docstatus": 1,
                        "status": "Active"
                }
        }
}
