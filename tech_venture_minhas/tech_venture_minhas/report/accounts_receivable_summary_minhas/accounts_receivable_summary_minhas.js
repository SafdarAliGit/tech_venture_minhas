

frappe.query_reports["Accounts Receivable Summary Minhas"] = {
	"filters": [
{
			"fieldname":"report_date",
			"label": __("Posting Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
	]

};
