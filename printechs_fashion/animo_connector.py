import requests
import frappe
import json
from frappe.utils import get_datetime


def test():
    print("animo_connector")

@frappe.whitelist()  
def send_sales_order_to_animo(doc, method):
    #doc, method
    """Fetches a sales order from ERPNext and sends it to the Animo API."""
    
    #order_name='SAL-ORD-2025-00099'
    # Fetch the sales order from ERPNext
    #doc = frappe.get_doc("Sales Order", order_name)
    
    frappe.logger().info(f"Triggered on_submit for Sales Order {doc.name}")
    # Prepare the JSON payload
    payload = {
        "Header": {
            "CompCode": "AR01C00001",
            "OrgCode": "1000",
            "OrderType": "OrderAPI",
            "SaleChannel": "SODAS ECOMM",
            "DocDate": str(get_datetime(doc.transaction_date).date()),
            "ReferenceNo": doc.name,
            "RefOrderNo": doc.name,
            "CustomerName": doc.customer_name,
            "EmailID": "customer@example.com",
            "PhoneNo": "9876543210",
            "BillingName": "Ecomm Customer",
            "BillingStreet": "123 Main Street",
            "BillingAddress1": "Suite 4B",
            "BillingZip": "560001",
            "BillingCountry": "SAUDI ARABIA",
            "ShippingName": "Ecomm Customer",
            "ShippingStreet": "123 Main Street",
            "ShippingAddress1": "Suite 4B",
            "ShippingZip": "560001",
            "ShippingCountry": "SAUDI ARABIA",
            "TaxMethod": "VAT-Inclusive",
            "ShippingMethod": "Standard",
            "ShippingStatus": "Pending",
            "PaymentMethod": "Prepaid",
            "PaymentStatus": "Paid",
            "ItemsCount": len(doc.items),
            "TotalQty": sum(item.qty for item in doc.items),
            "BasicAmt": doc.base_total,
            "Discount": doc.discount_amount,
            "TaxAmt": doc.total_taxes_and_charges,
            "SubTotal": doc.base_total,
            "RoundOff": doc.rounding_adjustment,
            "Total": doc.grand_total,
            "Remarks": "Deliver ASAP",
            "User": "order_api_user"
        },
        "Items": [
            {
                "sl": idx + 1,
                "Barcode": item.item_code,
                "Qty": item.qty,
                "Rate": item.rate,
                "BatchNo": "NA",
                "SerialNo": "NA",
                "ItemDesc": item.item_name,
                "Amount": item.amount,
                "Discount": item.discount_amount if item.discount_amount else 0,
                "TaxAmt": (item.amount - item.discount_amount if item.discount_amount else item.amount) * (15 / 100),
                "ItemTotal": item.amount,
                "TaxableValue": (item.amount - item.discount_amount if item.discount_amount else item.amount),
                "TaxPercent": 15
            }
            for idx, item in enumerate(doc.items)
        ]
    }
    print(payload)
    # Send request to Animo API
 
    url = "http://sodanimo.dyndns.org:8001/api/Order/CreateOrder"
    auth = ("jay", "123")
    headers = {"Content-Type": "application/json"}
   
    try:
        # Send request to Animo API
        response = requests.post(url, json=payload, auth=auth, headers=headers)
        response_status = response.status_code
        response_json = response.json() if response_status == 201 else {"error": response.text}
        
        # Logging
        if response_status == 201:
            frappe.logger().info(f"Sales Order {doc.name} sent successfully. Status: {response_status}")
            str_response_status='Success'
        else:
            frappe.logger().error(f"Failed to send Sales Order {doc.name}. Error: {response.text}")
            str_response_status='Failed'
        
        # Save response and status in Sales Order
        doc.custom_animo_api_status = str_response_status
        doc.custom_animo_api_response = json.dumps(response_json, indent=4)

        doc.save()  # Commit changes to the database
    except Exception as e:
        frappe.logger().error(f"Error in sending Sales Order {doc.name}: {str(e)}")
        doc.custom_animo_api_status = "Error"
        doc.custom_animo_api_response = str(e)
        doc.save()

@frappe.whitelist()
def send_sales_invoice_to_animo(doc, method):
    #doc, method
    """Fetches a Sales Invoice from ERPNext and sends it to the Animo API."""
    
    #invoice_name='ACC-SINV-2025-00044'
    # Fetch the sales order from ERPNext
    #doc = frappe.get_doc("Sales Invoice", invoice_name)
    
    frappe.logger().info(f"Triggered on_submit for Sales Invoice {doc.name}")
    
    # Prepare the JSON payload
    # Get the first item's Sales Order reference (assuming invoice is linked to a single Sales Order)
    reference_no = doc.items[0].sales_order if doc.items and hasattr(doc.items[0], "sales_order") else "Unknown"
    if doc.is_return==1:
        reference_no=doc.return_against

    payload = {
        "Header": {
            "CompCode": "AR01C00001",
            "OrgCode": "1000",
            "OrderType": "InvoiceAPI",
            "SaleChannel": "SODAS ECOMM",
            "DocDate": str(get_datetime(doc.posting_date).date()),  # Sales Invoice has posting_date
            "ReferenceNo": reference_no,
            "RefOrderNo": doc.name,
            "CustomerName": doc.customer_name,
            "EmailID": "customer@example.com",
            "PhoneNo": "9876543210",
            "BillingName": "Ecomm Customer",
            "BillingStreet": "123 Main Street",
            "BillingAddress1": "Suite 4B",
            "BillingZip": "560001",
            "BillingCountry": "SAUDI ARABIA",
            "ShippingName": "Ecomm Customer",
            "ShippingStreet": "123 Main Street",
            "ShippingAddress1": "Suite 4B",
            "ShippingZip": "560001",
            "ShippingCountry": "SAUDI ARABIA",
            "TaxMethod": "VAT-Inclusive",
            "ShippingMethod": "Standard",
            "ShippingStatus": "Pending",
            "PaymentMethod": "Prepaid",
            "PaymentStatus": "Paid",
            "ItemsCount": len(doc.items),
            "TotalQty": abs(sum(item.qty for item in doc.items)),
            "BasicAmt": abs(doc.base_total),
            "Discount": abs(doc.discount_amount),
            "TaxAmt": abs(doc.total_taxes_and_charges),
            "SubTotal": abs(doc.base_total),
            "RoundOff": abs(doc.rounding_adjustment),
            "Total": abs(doc.grand_total),
            "Remarks": doc.remarks if doc.remarks else "Deliver ASAP",
            "User": "invoice_api_user"
        },
        "Items": [
            {
                "sl": idx + 1,
                "Barcode": item.item_code,
                "Qty": abs(item.qty),
                "Rate": abs(item.rate),
                "BatchNo": "NA",
                "SerialNo": "NA",
                "ItemDesc": item.item_name,
                "Amount": abs(item.amount),
                "Discount": abs(item.discount_amount if item.discount_amount else 0),
                "TaxAmt": abs((item.amount - item.discount_amount if item.discount_amount else item.amount) * (15 / 100)),
                "ItemTotal": abs(item.amount),
                "TaxableValue": abs(item.amount - item.discount_amount if item.discount_amount else item.amount),
                "TaxPercent": 15
            }
            for idx, item in enumerate(doc.items)
        ]
    }
    
    print(payload)
    
    # Send request to Animo API
    url=""
    
    if doc.is_return==1:
        url = "http://sodanimo.dyndns.org:8001/api/Order/CreateSaleReturn"
    else:
        url = "http://sodanimo.dyndns.org:8001/api/Order/CreateSaleInvoice"
        
    auth = ("jay", "123")
    headers = {"Content-Type": "application/json"}
   
    try:
        response = requests.post(url, json=payload, auth=auth, headers=headers)
        response_status = response.status_code
        response_json = response.json() if response_status == 201 else {"error": response.text}
        
        # Logging
        if response_status == 201:
            frappe.logger().info(f"Sales Invoice {doc.name} sent successfully. Status: {response_status}")
            str_response_status = "Success"
        else:
            frappe.logger().error(f"Failed to send Sales Invoice {doc.name}. Error: {response.text}")
            str_response_status = "Failed"
        doc.reload()
        # Save response and status in Sales Invoice
        doc.custom_animo_api_status = str_response_status
        doc.custom_animo_api_response = json.dumps(response_json, indent=4)

        doc.save()  # Commit changes to the database
    except Exception as e:
        frappe.logger().error(f"Error in sending Sales Invoice {doc.name}: {str(e)}")
        doc.custom_animo_api_status = "Error"
        doc.custom_animo_api_response = str(e)
        doc.save()
