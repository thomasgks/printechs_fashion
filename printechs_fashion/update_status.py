# File: delivery_note.py (custom app or override)
from frappe.model.document import Document
import frappe

def update_return_status_dn(delivery_note, status):
    if not delivery_note.is_return:
        return

    # Track affected Sales Orders
    affected_sales_orders = set()

    for item in delivery_note.items:
        if item.against_sales_order:
            affected_sales_orders.add(item.against_sales_order)

            # Update return_status in Sales Order Item
            frappe.db.set_value(
                "Sales Order Item",
                {"parent": item.against_sales_order, "name": item.so_detail},
                "custom_return_status",
                status
            )

    # Update return_status in Sales Order
    for so in affected_sales_orders:
        frappe.db.set_value("Sales Order", so, "custom_return_status", status)

# Hook: on_submit
def on_submit_dn(doc, method):
    update_return_status_dn(doc, "Received")

# Hook: on_cancel
def on_cancel_dn(doc, method):
    update_return_status_dn(doc, "Rejected")



def update_return_status_si(invoice, status):
    if not invoice.is_return:
        return

    affected_sales_orders = set()

    for item in invoice.items:
        if item.sales_order:
            affected_sales_orders.add(item.sales_order)

            # Update return_status in Sales Order Item
            frappe.db.set_value(
                "Sales Order Item",
                {"parent": item.sales_order, "name": item.so_detail},
                "custom_return_status",
                status
            )

    # Update return_status in Sales Order
    for so in affected_sales_orders:
        frappe.db.set_value("Sales Order", so, "custom_return_status", status)

# Hook: on_submit
def on_submit_si(doc, method):
    update_return_status_si(doc, "Refund Initiated")

# Hook: on_cancel
def on_cancel_si(doc, method):
    update_return_status_si(doc, "Received")
