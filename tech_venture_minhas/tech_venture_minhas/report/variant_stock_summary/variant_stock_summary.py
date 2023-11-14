import frappe
from frappe import _


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
            "label": _("Variant Of"),
            "fieldname": "variant_of",
            "fieldtype": "Data",
            "width": 200
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
            "label": _("Qty After Transaction"),
            "fieldname": "qty_after_transaction",
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


def get_data(filters):
    data = []
    stock_query = """
            SELECT 
                `tabItem`.variant_of,
                SUM(`tabStock Ledger Entry`.actual_qty) AS actual_qty,
                SUM(`tabStock Ledger Entry`.qty_after_transaction) AS qty_after_transaction
            FROM 
                `tabItem`,`tabStock Ledger Entry`
            WHERE `tabItem`.item_code = `tabStock Ledger Entry`.item_code 
                AND `tabStock Ledger Entry`.docstatus < 2 
                AND `tabStock Ledger Entry`.is_cancelled = 0 
                AND {conditions}
            GROUP BY `tabItem`.variant_of
            """.format(conditions=get_conditions(filters, "Stock Ledger Entry"))
    # WHERE
    #      {conditions}
    # GROUP BY `tabSales Invoice`.customer_group, `tabSales Invoice`.customer
    # .format(conditions=get_conditions(filters, "Sales Invoice"))

    # si_result = frappe.db.sql(si_query, filters, as_dict=1)
    stock_result = frappe.db.sql(stock_query,filters, as_dict=1)
    # total_no_of_bills = 0
    # total_bill_amount = 0
    # total_customer_name = len(si_result)
    # for row in si_result:
    #     total_no_of_bills += row["no_of_bills"]
    #     total_bill_amount += row["bill_amount"]
    # si_result.append({
    #     "customer_group": _("Total"),
    #     "customer_name": f"Total parties :  {total_customer_name}",
    #     "no_of_bills": total_no_of_bills,
    #     "bill_amount": total_bill_amount
    # })
    for item in stock_result:
        item.update({"in_qty": max(item.actual_qty, 0), "out_qty": min(item.actual_qty, 0)})
    data.extend(stock_result)
    return data





