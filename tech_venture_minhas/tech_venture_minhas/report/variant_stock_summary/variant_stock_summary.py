from collections import defaultdict

import frappe
from frappe import _
from itertools import groupby
from operator import itemgetter


def execute(filters=None):
    if not filters:
        filters = {}
    data = []
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def decimal_format(value, decimals):
    formatted_value = "{:.{}f}".format(value, decimals)
    return formatted_value


def get_columns():
    columns = [
        {
            "label": _("Item Template"),
            "fieldname": "variant_of",
            "fieldtype": "Data",
            "width": 200
        },
        {
            "label": _("Opening Stock"),
            "fieldname": "qty_after_transaction",
            "fieldtype": "Float",
            "width": 80,
            "convertible": "qty",
        },
        {
            "label": _("In Qty"),
            "fieldname": "in_qty",
            "fieldtype": "Float",
            "width": 80,
            "convertible": "qty",
        },
        {
            "label": _("Out Qty"),
            "fieldname": "out_qty",
            "fieldtype": "Float",
            "width": 80,
            "convertible": "qty",
        },
        {
            "label": _("Qty Balance"),
            "fieldname": "qty_balance",
            "fieldtype": "Data",
            "width": 200
        }
        # {
        #     "label": _("Party"),
        #     "fieldname": "customer_name",
        #     "fieldtype": "Data",
        #     "width": 200
        # },
        # {
        #     "label": _("No Of Bills"),
        #     "fieldname": "no_of_bills",
        #     "fieldtype": "Data",
        #     "width": 80
        # },
        # {
        #     "label": _("Bill Amount"),
        #     "fieldname": "bill_amount",
        #     "fieldtype": "Currency",
        #     "width": 200
        # }

    ]
    return columns


def get_conditions(filters, doctype):
    conditions = []

    if filters.get("from_date"):
        conditions.append(f"`tab{doctype}`.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append(f"`tab{doctype}`.posting_date <= %(to_date)s")
    if filters.get("variant_of"):
        conditions.append(f"`tabItem`.variant_of = %(variant_of)s")
    return " AND ".join(conditions)


def get_other_conditions(filters, doctype):
    conditions = []
    if filters.get("to_date"):
        conditions.append(f"`tab{doctype}`.posting_date > %(to_date)s")
    if filters.get("variant_of"):
        conditions.append(f"`tabItem`.variant_of = %(variant_of)s")
    return " AND ".join(conditions)


def get_data(filters):
    data = []
    stock_query = """
            SELECT 
                `tabItem`.variant_of,
                `tabStock Ledger Entry`.actual_qty
            FROM 
                `tabItem`,`tabStock Ledger Entry`
            WHERE `tabItem`.item_code = `tabStock Ledger Entry`.item_code 
                AND `tabStock Ledger Entry`.docstatus < 2 
                AND `tabStock Ledger Entry`.is_cancelled = 0 
                AND {conditions}
            """.format(conditions=get_conditions(filters, "Stock Ledger Entry"))
    stock_result = frappe.db.sql(stock_query, filters, as_dict=1)

    other_stock_query = """
                SELECT 
                    `tabItem`.variant_of,
                    SUM(`tabStock Ledger Entry`.qty_after_transaction) AS qty_after_transaction
                FROM 
                    `tabItem`, `tabStock Ledger Entry`
                WHERE 
                    `tabItem`.item_code = `tabStock Ledger Entry`.item_code 
                    AND `tabStock Ledger Entry`.docstatus < 2 
                    AND `tabStock Ledger Entry`.is_cancelled = 0 
                    AND {conditions}
                GROUP BY
                    `tabItem`.variant_of
            """.format(conditions=get_other_conditions(filters, "Stock Ledger Entry"))
    other_stock_result = frappe.db.sql(other_stock_query, filters, as_dict=1)

    for item in stock_result:
        item["in_qty"] = max(item["actual_qty"], 0)
        item["out_qty"] = min(item["actual_qty"], 0)

    grouped_data = defaultdict(lambda: {"in_qty": 0, "out_qty": 0})

    for item in stock_result:
        grouped_data[item["variant_of"]]["in_qty"] += item["in_qty"]
        grouped_data[item["variant_of"]]["out_qty"] += item["out_qty"]

    # Convert defaultdict to a list of dictionaries
    grouped_data_list = [{"variant_of": key, **values} for key, values in grouped_data.items()]

    for d in grouped_data_list:
        d["qty_balance"] = d["in_qty"] + d["out_qty"]
        # OTHER CALCULATIONS HERE
    for item in grouped_data_list:
        matching_item = next((x for x in other_stock_result if x['variant_of'] == item['variant_of']), None)
        if matching_item:
            item.update({'qty_after_transaction': matching_item['qty_after_transaction']})
        # OTHER CLACULATIONS END

    data.extend(grouped_data_list)
    return data
