// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["LTC Process Report"] = {
  filters: [
    {
      fieldname: "fiscal_year",
      label: __("Fiscal Year"),
      fieldtype: "Link",
      options: "Fiscal Year",
      default: frappe.defaults.get_user_default("fiscal_year"),
      reqd: 1
    },
    {
      fieldname: "ltc_type",
      label: __("LTC"),
      fieldtype: "Select",
      options: ["LTC"],
      default: "LTC",
      reqd: 1
    }
  ]
};
