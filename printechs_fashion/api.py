import frappe
from frappe import _
from frappe.model.document import Document

def test():
    print("OK")

@frappe.whitelist()
def check_item_attribute_value(attribute_value, parent):
    try:
        # Query to check if the attribute value exists
        exists = frappe.db.exists({
            "doctype": "Item Attribute Value",
            "attribute_value": attribute_value,
            "parent": parent
        })

        return {
            "status": "success",
            "exists": bool(exists)
        }
    except Exception as e:
        frappe.log_error(message=e, title="Item Attribute Value Check Error")
        return {
            "status": "error",
            "message": str(e)
        }
        
@frappe.whitelist()
def insert_item_attribute_value_temp(attribute_value, abbr, parent):
    try:
        # Create a new Item Attribute Value document
        item_attribute_value = frappe.get_doc({
            "doctype": "Item Attribute Value",
            "attribute_value": attribute_value,
            "abbr": abbr,
            "parent": parent,
            "parentfield": "item_attribute_values",
            "parenttype": "Item Attribute"
        })
        item_attribute_value.insert()
        frappe.db.commit()

        return {
            "status": "success",
            "message": _("Item Attribute Value inserted successfully"),
            "data": item_attribute_value.as_dict()
        }
    except Exception as e:
        frappe.log_error(message=e, title="Item Attribute Value Insertion Error")
        return {
            "status": "error",
            "message": str(e)
        }
    
@frappe.whitelist()
def insert_item_attribute_value(attribute_value, abbr, parent):
    try:
        # Check if the attribute value exists
        exists = frappe.db.exists({
            "doctype": "Item Attribute Value",
            "attribute_value": attribute_value,
            "parent": parent
        })

        if exists:
            return {
                "status": "success",
                "message": _("Item Attribute Value already exists")
            }

        # Create a new Item Attribute Value document if it doesn't exist
        item_attribute_value = frappe.get_doc({
            "doctype": "Item Attribute Value",
            "attribute_value": attribute_value,
            "abbr": abbr,
            "parent": parent,
            "parentfield": "item_attribute_values",
            "parenttype": "Item Attribute"
        })
        item_attribute_value.insert()
        frappe.db.commit()

        return {
            "status": "success",
            "message": _("Item Attribute Value inserted successfully"),
            "data": item_attribute_value.as_dict()
        }
    except Exception as e:
        frappe.log_error(message=e, title="Item Attribute Value Insertion Error")
        return {
            "status": "error",
            "message": str(e)
        }
