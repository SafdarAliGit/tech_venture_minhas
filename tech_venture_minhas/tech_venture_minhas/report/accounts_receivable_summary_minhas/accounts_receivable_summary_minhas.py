# Copyright (c) 2023, Tech Venture and contributors
# For license information, please see license.txt
import frappe
from erpnext.accounts.doctype.cost_center import cost_center
from erpnext.accounts.utils import get_fiscal_year, FiscalYearError
from frappe import cstr
from frappe.utils import nowdate, getdate, flt


# import frappe


def execute(filters=None):
    return get_columns(filters), get_data(filters)


def get_data(filters):
    data = frappe.db.sql(
        """
        SELECT 
            gle.party, 
            SUM(gle.debit) - SUM(gle.credit) AS outstanding,
             cust.customer_group, 
            gle.account_currency AS currency
        FROM 
            `tabGL Entry` gle
        JOIN
            `tabCustomer` cust ON cust.name = gle.party  
        WHERE 
            gle.posting_date <= %(nowdate)s 
            AND gle.docstatus = 1
        GROUP BY 
            gle.party
        """,
        {"nowdate": filters.get("report_date")},as_dict=1,
    )
    filtered_array = [d for d in data if d.get('outstanding') != 0]
    return filtered_array


def get_columns(filters):
    columns = [
        {
            "fieldname": "party",
            "fieldtype": "Link",
            "options": "Customer",
            "label": "Party",
            "width": 200
        },
        {
            "fieldname": "outstanding",
            "fieldtype": "Currency",
            "label": "Outstanding",
            "width": 150
        },
        {
            "fieldname": "customer_group",
            "fieldtype": "Data",
            "label": "Customer Group",
            "width": 150

        },
        {
            "fieldname": "currency",
            "fieldtype": "Data",
            "label": "Currency",
            "width": 150
        }
    ]

    return columns
