frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Today Leave By Department"] = {
	method: "hrms.hr.dashboard_chart_source.today_leave_by_department.today_leave_by_department.get_data",
	filters: []
};