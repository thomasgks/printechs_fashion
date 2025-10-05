# animo_connector.py
import json
import requests
import frappe
from frappe.utils import get_datetime
from frappe.utils.background_jobs import enqueue
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential

# Constants
ANIMO_API_CREDENTIALS_TEST = ("admin", "Animo@1")
API_TIMEOUT = 30  # seconds
MAX_RETRIES = 3

# Status tracking
SYNC_STATUSES = {
    "QUEUED": "Queued",
    "PROCESSING": "Processing",
    "SUCCESS": "Success",
    "FAILED": "Failed",
    "CONNECTION_ERROR": "Connection Error"
}
@frappe.whitelist()
def setup_custom_fields():
    """Create custom fields if they don't exist"""
    custom_fields = {
        "Sales Order": [
            {
                "fieldname": "custom_animo_sync_status",
                "label": "Animo Sync Status",
                "fieldtype": "Select",
                "options": "\n".join(SYNC_STATUSES.values()),
                "insert_after": "is_internal_customer",
                "read_only": 1
            },
            {
                "fieldname": "custom_animo_last_sync",
                "label": "Animo Last Sync",
                "fieldtype": "Datetime",
                "insert_after": "custom_animo_sync_status",
                "read_only": 1
            },
            {
                "fieldname": "custom_animo_retry_count",
                "label": "Animo Retry Count",
                "fieldtype": "Int",
                "insert_after": "custom_animo_last_sync",
                "read_only": 1,
                "default": 0
            }
        ],
        "Sales Invoice": [
            {
                "fieldname": "custom_animo_sync_status",
                "label": "Animo Sync Status",
                "fieldtype": "Select",
                "options": "\n".join(SYNC_STATUSES.values()),
                "insert_after": "is_internal_customer",
                "read_only": 1
            },
            {
                "fieldname": "custom_animo_last_sync",
                "label": "Animo Last Sync",
                "fieldtype": "Datetime",
                "insert_after": "custom_animo_sync_status",
                "read_only": 1
            },
            {
                "fieldname": "custom_animo_retry_count",
                "label": "Animo Retry Count",
                "fieldtype": "Int",
                "insert_after": "custom_animo_last_sync",
                "read_only": 1,
                "default": 0
            }
        ]
    }

    for doctype, fields in custom_fields.items():
        for field in fields:
            if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
                frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": doctype,
                    **field
                }).insert(ignore_permissions=True)

def update_doc_status(doc, status, response=None, increment_retry=False, payload=None):
    """
    Update document sync status without retry logic
    Uses direct database update as primary method with fallback to doc.save()
    """
    try:
        # Get document reference
        docname = doc.name if hasattr(doc, 'name') else doc
        doctype = doc.doctype if hasattr(doc, 'doctype') else "Sales Order"
        
        # Prepare update values
        update_values = {
            "custom_animo_sync_status": status,
            "custom_animo_last_sync": frappe.utils.now(),
            "modified": frappe.utils.now()
        }
        
        if increment_retry:
            current_count = frappe.db.get_value(doctype, docname, "custom_animo_retry_count") or 0
            update_values["custom_animo_retry_count"] = current_count + 1
        
        if response is not None:
            update_values["custom_animo_api_response"] = json.dumps(response, indent=2)
        
        if payload is not None:
            update_values["custom_animo_api_payload"] = json.dumps(payload, indent=2)
        
        # Try direct SQL update first (most reliable)
        frappe.db.set_value(doctype, docname, update_values)
        frappe.db.commit()
        
        # Verify update
        updated_status = frappe.db.get_value(doctype, docname, "custom_animo_sync_status")
        if updated_status == status:
            return True
            
        # If direct update didn't work, try document save
        doc = frappe.get_doc(doctype, docname)
        for field, value in update_values.items():
            if doc.meta.has_field(field):
                doc.set(field, value)
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        return True
        
    except Exception as e:
        frappe.logger().error(
            f"Failed to update {doctype} {docname} status to {status}\n"
            f"Error: {str(e)}\n"
            f"Response: {response}"
        )
        frappe.db.rollback()
        return False
# def update_doc_status(doc, status, response=None, increment_retry=False,payload=None):
#     """Update document sync status and log response"""
#     doc.reload()
#     doc.custom_animo_sync_status = status
#     doc.custom_animo_last_sync = frappe.utils.now()
    
#     if increment_retry:
#         doc.custom_animo_retry_count = (doc.custom_animo_retry_count or 0) + 1
    
#     if response:
#         doc.custom_animo_api_response = json.dumps(response, indent=2)
#     if payload:
#         doc.custom_animo_api_payload = json.dumps(payload, indent=4)
    
#     doc.save(ignore_permissions=True)
#     frappe.db.commit()

def log_comment(doc, title, content):
    """Add a comment to the document"""
    comment = frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Comment",
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "content": f"<b>[ANIMO {title}]</b><br>{content}"
    })
    comment.insert(ignore_permissions=True)

# API Call Decorator
@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
def make_animo_api_call(url, payload):
    """Make API call with retry logic"""
    settings = frappe.get_single("Animo Setting")
    ANIMO_API_CREDENTIALS = (settings.username, settings.get_password("password"))
    print(ANIMO_API_CREDENTIALS)
    response = requests.post(
        url,
        json=payload,
        auth=ANIMO_API_CREDENTIALS,
        headers={"Content-Type": "application/json"},
        timeout=API_TIMEOUT
    )
    print(response)
    print(response.text)
    response.raise_for_status()
    return response.json()

# Document Event Handlers
@frappe.whitelist()
def enqueue_animo_order_sync(doc, method):
    """Enqueue Sales Order sync with Animo"""
    if isinstance(doc, str):
        doc = frappe.get_doc("Sales Order", doc)
     # Skip if already successfully synced
    print(doc.get("custom_animo_sync_status"))
    if doc.get("custom_animo_sync_status") == "Success":
        log_comment(doc, "Animo Sync", "Already synced successfully - skipping")
        return
    
    setup_custom_fields()
    update_doc_status(doc, SYNC_STATUSES["QUEUED"])
    
    enqueue(
        "printechs_fashion.animo_connector.sync_sales_order_with_animo",
        queue="default",
        timeout=600,
        is_async=True,
        enqueue_after_commit=True,
        docname=doc.name
    )

@frappe.whitelist()
def enqueue_animo_invoice_sync(doc, method):
    """Enqueue Sales Invoice sync with Animo"""
    if isinstance(doc, str):
        doc = frappe.get_doc("Sales Invoice", doc)
     # Skip if already successfully synced
    if doc.get("custom_animo_sync_status") == "Success":
        log_comment(doc, "Animo Sync", "Already synced successfully - skipping")
        return
    setup_custom_fields()
    update_doc_status(doc, SYNC_STATUSES["QUEUED"])
    
    enqueue(
        "printechs_fashion.animo_connector.sync_sales_invoice_with_animo",
        queue="default",
        timeout=600,
        is_async=True,
        enqueue_after_commit=True,
        docname=doc.name
    )

@frappe.whitelist()
def enqueue_animo_order_cancel(doc, method):
    """Enqueue Sales Order cancellation with Animo"""
    if isinstance(doc, str):
        doc = frappe.get_doc("Sales Order", doc)
     # Skip if already successfully synced
    # if doc.get("custom_animo_sync_status") == "Success":
    #     log_comment(doc, "Animo Sync", "Already synced successfully - skipping")
    #     return
    
    enqueue(
        "printechs_fashion.animo_connector.cancel_sales_order_with_animo",
        queue="default",
        timeout=600,
        is_async=True,
        enqueue_after_commit=True,
        docname=doc.name
    )

# Background Job Functions
def sync_sales_order_with_animo(docname):
    """Background job to sync Sales Order with Animo"""
    try:
        doc = frappe.get_doc("Sales Order", docname)
        
        # Set status to Processing immediately
        update_doc_status(doc, SYNC_STATUSES["PROCESSING"])
        
        payload = prepare_sales_order_payload(doc)
        
        settings = frappe.get_single("Animo Setting")
        url = settings.animo_api_base_url + "/api/Order/CreateOrder"
        
        response = make_animo_api_call(url, payload)
        
        # Check for specific success response pattern
        if isinstance(response, dict) and response.get("orderID", "").startswith("Sales Order No :"):
            update_doc_status(doc, SYNC_STATUSES["SUCCESS"], response, payload=payload)
            log_comment(doc, "Sync Success", f"Order synced successfully with Animo. Response: {response}")
        else:
            # Handle unexpected response format
            error_msg = f"Unexpected response format from Animo: {response}"
            frappe.logger().error(error_msg)
            update_doc_status(doc, SYNC_STATUSES["FAILED"], {"error": error_msg}, increment_retry=True, payload=payload)
            log_comment(doc, "Sync Failed", error_msg)
            
    except RequestException as e:
        error_msg = f"Animo API connection error: {str(e)}"
        frappe.logger().error(error_msg)
        doc = frappe.get_doc("Sales Order", docname)
        update_doc_status(doc, SYNC_STATUSES["CONNECTION_ERROR"], {"error": str(e)}, increment_retry=True, payload=payload)
        log_comment(doc, "Sync Failed", error_msg)
        
    except Exception as e:
        error_msg = f"Animo API error: {str(e)}"
        frappe.logger().error(error_msg)
        doc = frappe.get_doc("Sales Order", docname)
        update_doc_status(doc, SYNC_STATUSES["FAILED"], {"error": str(e)}, increment_retry=True, payload=payload)
        log_comment(doc, "Sync Failed", error_msg)

def sync_sales_invoice_with_animo(docname):
    """Background job to sync Sales Invoice with Animo"""
    doc = frappe.get_doc("Sales Invoice", docname)
    update_doc_status(doc, SYNC_STATUSES["PROCESSING"])
    payload = None
    
    try:
        payload = prepare_sales_invoice_payload(doc)
        print(payload)
        settings = frappe.get_single("Animo Setting")
        base_url = settings.animo_api_base_url 
        url=""
        # Determine the appropriate API endpoint
        if doc.is_return == 1:
            url = base_url + "/api/Order/CreateSaleReturn"
            success_pattern = "Sales Return No :"
        else:
            url = base_url + "/api/Order/CreateSaleInvoice"
            success_pattern = "Sales Invoice No :"
        
        response = make_animo_api_call(url, payload)
        print(response)
        
        # Improved success checking logic
        if (isinstance(response, dict) and "orderID" in response and 
            isinstance(response["orderID"], str) and 
            "Duplicate Document" in response["orderID"] and 
            "already exists" in response["orderID"]):
            
            # Treat duplicate as success since it means the document was already synced
            update_doc_status(doc, SYNC_STATUSES["SUCCESS"], response, payload=payload)
            log_comment(doc, "Sync Success", f"Document already exists in Animo: {response['orderID']}")
            
        # Check for normal success response
        elif (isinstance(response, dict) and 
            response.get("orderID", "") and 
            success_pattern in response["orderID"] and 
            "successfully" in response["orderID"]):
            update_doc_status(doc, SYNC_STATUSES["SUCCESS"], response, payload=payload)
            log_comment(doc, "Sync Success", f"Invoice synced successfully with Animo. Response: {response}")
        else:
            # Handle unexpected response format
            error_msg = f"Unexpected response format from Animo: {response}"
            frappe.logger().error(error_msg)
            update_doc_status(doc, SYNC_STATUSES["FAILED"], {"error": error_msg}, increment_retry=True, payload=payload)
            log_comment(doc, "Sync Failed", error_msg)
            
    except RequestException as e:
        error_msg = f"Animo API connection error: {str(e)}"
        frappe.logger().error(error_msg)
        doc = frappe.get_doc("Sales Invoice", docname)
        update_doc_status(doc, SYNC_STATUSES["CONNECTION_ERROR"], {"error": str(e)}, increment_retry=True, payload=payload)
        log_comment(doc, "Sync Failed", error_msg)
        
    except Exception as e:
        error_msg = f"Animo API error: {str(e)}"
        frappe.logger().error(error_msg)
        doc = frappe.get_doc("Sales Invoice", docname)
        update_doc_status(doc, SYNC_STATUSES["FAILED"], {"error": str(e)}, increment_retry=True, payload=payload)
        log_comment(doc, "Sync Failed", error_msg)

def cancel_sales_order_with_animo(docname):
    """Background job to cancel Sales Order with Animo"""
    doc = frappe.get_doc("Sales Order", docname)
    
    try:
        payload = {
            "CompCode": "AR01C00001",
            "OrgCode": "1010",
            "DocNo": doc.name,
            "User": "order_api_user"
        }
        
        settings = frappe.get_single("Animo Setting")
        url = settings.animo_api_base_url + "/api/Order/CancelOrder"
        
        response = make_animo_api_call(url, payload)
        
        log_comment(doc, "Cancel Success", f"Order cancelled successfully with Animo[{json.dumps(response, indent=2)}]")
        return response
        
    except RequestException as e:
        frappe.logger().error(f"Animo API connection error during cancellation for {doc.name}: {str(e)}")
        log_comment(doc, "Cancel Failed", f"Connection error: {str(e)}")
        raise
        
    except Exception as e:
        frappe.logger().error(f"Animo API error during cancellation for {doc.name}: {str(e)}")
        log_comment(doc, "Cancel Failed", f"Error: {str(e)}")
        raise

# Payload Preparation Functions
def prepare_sales_order_payload(doc):
    """Prepare payload for Sales Order with precise tax calculation"""
    address = None
    if doc.customer_address:
        address = frappe.get_doc("Address", doc.customer_address)
    contact = frappe.get_doc("Contact", doc.contact_person)
    
    # Calculate base amounts
    basic_amt = sum(item.price_list_rate * item.qty for item in doc.items)
    item_level_discount = sum(item.discount_amount * item.qty or 0 for item in doc.items)
    global_discount = doc.discount_amount or 0
    total_discount = item_level_discount + global_discount
    
    # Calculate item taxes first
    items = []
    total_item_tax = 0
    
    for idx, item in enumerate(doc.items):
        gross_amount = item.qty * item.price_list_rate
        discount = calculate_discount((item.qty * item.discount_amount), item.distributed_discount_amount)
        item_total = gross_amount - discount
        tax = calculate_tax_amount(gross_amount, discount)
        total_item_tax += tax
        
        items.append({
            "sl": idx + 1,
            "Barcode": item.item_code,
            "Qty": item.qty,
            "Rate": item.price_list_rate,
            "BatchNo": "NA",
            "SerialNo": "NA",
            "ItemDesc": item.item_name,
            "Amount": gross_amount,
            "Discount": discount,
            "TaxAmt": round(tax, 2),
            "ItemTotal": round(item_total, 2),
            "TaxableValue": round(item_total - tax, 2),
            "TaxPercent": 15
        })

    # Calculate header tax amount based on items to ensure consistency
    header_tax_amt = round(total_item_tax, 2)
    
    payload = {
        "Header": {
            "CompCode": "AR01C00001",
            "OrgCode": "1010",
            "OrderType": "OrderAPI",
            "SaleChannel": "SODAS ECOMM",
            "DocDate": str(get_datetime(doc.transaction_date).date()),
            "ReferenceNo": doc.name,
            "RefOrderNo": doc.name,
            "CustomerName": doc.customer_name,
            "EmailID": contact.email_id or "customer@example.com",
            "PhoneNo": contact.phone or "9876543210",
            "BillingName": doc.customer_name,
            "BillingStreet":   address.address_line2 if address and address.address_line2 else "",
            "BillingAddress1": address.address_line1 if address and address.address_line1 else "",
            "BillingZip": address.pincode if address and address.pincode else "",
            "BillingCountry": address.country if address and address.country else "",
            "ShippingName": doc.customer_name,
            "ShippingStreet": address.address_line2 if address and address.address_line2 else "",
            "ShippingAddress1": address.address_line1 if address and address.address_line1 else "",
            "ShippingZip": address.pincode if address and address.pincode else "",
            "ShippingCountry": address.country if address and address.country else "",
            "TaxMethod": "VAT-Inclusive",
            "ShippingMethod": "Standard",
            "ShippingStatus": "Pending",
            "PaymentMethod": "Prepaid",
            "PaymentStatus": "Paid",
            "ItemsCount": len(doc.items),
            "TotalQty": sum(item.qty for item in doc.items),
            "BasicAmt": round(basic_amt, 2),
            "Discount": round(total_discount, 2),
            "TaxAmt": header_tax_amt,  # Use the sum of item taxes
            "charges": round(doc.total_taxes_and_charges, 2),
            "SubTotal": round((basic_amt - total_discount) + doc.total_taxes_and_charges, 2),
            "RoundOff": round(doc.rounding_adjustment, 2),
            "Total": round(doc.grand_total, 2),
            "Remarks": "Deliver ASAP",
            "User": "order_api_user"
        },
        "Items": items
    }

    return payload

def prepare_sales_invoice_payload_old(doc):
    """Prepare payload for Sales Invoice with precise tax calculation"""
    reference_no = doc.items[0].sales_order if doc.items and hasattr(doc.items[0], "sales_order") else doc.name
    print(reference_no)
    # if doc.is_return == 1:
    #     reference_no = doc.return_against

    address = frappe.get_doc("Address", doc.customer_address)
    contact = frappe.get_doc("Contact", doc.contact_person)
    
    # Calculate base amounts
    basic_amt = sum(item.price_list_rate * item.qty for item in doc.items)
    item_level_discount = sum(item.discount_amount * item.qty or 0 for item in doc.items)
    global_discount = doc.discount_amount or 0
    total_discount = item_level_discount + global_discount
    
    # Calculate item taxes first
    items = []
    total_item_tax = 0
    
    for idx, item in enumerate(doc.items):
        gross_amount = item.qty * item.price_list_rate
        discount = calculate_discount((item.qty * item.discount_amount), item.distributed_discount_amount)
        item_total = gross_amount - discount
        tax = calculate_tax_amount(gross_amount, discount)
        total_item_tax += tax
        
        items.append({
            "sl": idx + 1,
            "Barcode": item.item_code,
            "Qty": item.qty,
            "Rate": item.price_list_rate,
            "BatchNo": "NA",
            "SerialNo": "NA",
            "ItemDesc": item.item_name,
            "Amount": round(gross_amount, 2),
            "Discount": round(discount, 2),
            "TaxAmt": round(tax, 2),
            "ItemTotal": round(item_total, 2),
            "TaxableValue": round(item_total - tax, 2),
            "TaxPercent": 15
        })

    # Calculate header tax amount based on items to ensure consistency
    header_tax_amt = round(total_item_tax, 2)
    
    payload = {
        "Header": {
            "CompCode": "AR01C00001",
            "OrgCode": "1010",
            "OrderType": "OrderAPI",
            "SaleChannel": "SODAS ECOMM",
            "DocDate": str(get_datetime(doc.posting_date).date()),
            "ReferenceNo": reference_no,
            "RefOrderNo": doc.name,
            "CustomerName": doc.customer_name,
            "EmailID": contact.email_id or "customer@example.com",
            "PhoneNo": contact.phone or "9876543210",
            "BillingName": doc.customer_name,
            "BillingStreet": address.address_line2 or "123 Main Street",
            "BillingAddress1": address.address_line1 or "Suite 4B",
            "BillingZip": address.pincode or "560001",
            "BillingCountry": address.country or "SAUDI ARABIA",
            "ShippingName": doc.customer_name,
            "ShippingStreet": address.address_line2 or "123 Main Street",
            "ShippingAddress1": address.address_line1 or "Suite 4B",
            "ShippingZip": address.pincode or "560001",
            "ShippingCountry": address.country or "SAUDI ARABIA",
            "TaxMethod": "VAT-Inclusive",
            "ShippingMethod": "Standard",
            "ShippingStatus": "Pending",
            "PaymentMethod": "Prepaid",
            "PaymentStatus": "Paid" if doc.outstanding_amount == 0 else "Pending",
            "ItemsCount": len(doc.items),
            "TotalQty": sum(item.qty for item in doc.items),
            "BasicAmt": round(basic_amt, 2),
            "Discount": round(total_discount, 2),
            "TaxAmt": header_tax_amt,  # Use the sum of item taxes
            "charges": round(doc.total_taxes_and_charges, 2),
            "SubTotal": round((basic_amt - total_discount) + doc.total_taxes_and_charges, 2),
            #"RoundOff": round(doc.rounding_adjustment, 2),
            "Total": round(doc.grand_total, 2),
            "Remarks": "Deliver ASAP",
            "User": "order_api_user"
        },
        "Items": items
    }
    return payload

def prepare_sales_invoice_payload(doc):
    """Prepare payload for Sales Invoice/Return with positive values for returns"""
    # Get reference number (original sales invoice for returns)
    reference_no = (doc.items[0].sales_order if doc.items and hasattr(doc.items[0], "sales_order") else doc.name)
    
    address = None
    if doc.customer_address:
        address = frappe.get_doc("Address", doc.customer_address)
    contact = frappe.get_doc("Contact", doc.contact_person)
    
    # Convert negative values to positive for returns
    convert_to_positive = 1 if doc.is_return == 1 else -1 if doc.is_debit_note == 1 else 1
    
    # Calculate base amounts (absolute values for returns)
    basic_amt = abs(sum(item.price_list_rate * item.qty for item in doc.items))
    item_level_discount = abs(sum(item.discount_amount * item.qty or 0 for item in doc.items))
    global_discount = abs(doc.discount_amount or 0)
    total_discount = item_level_discount + global_discount
    
    # Calculate item taxes first
    items = []
    total_item_tax = 0
    
    for idx, item in enumerate(doc.items):
        gross_amount = abs(item.qty * item.price_list_rate)
        discount = abs(calculate_discount((item.qty * item.discount_amount), item.distributed_discount_amount))
        item_total = gross_amount - discount
        tax = abs(calculate_tax_amount(gross_amount, discount))
        total_item_tax += tax
        
        items.append({
            "sl": idx + 1,
            "Barcode": item.item_code,
            "Qty": abs(item.qty),  # Positive quantity
            "Rate": abs(item.price_list_rate),  # Positive rate
            "BatchNo": item.batch_no or "NA",
            "SerialNo": item.serial_no or "NA",
            "ItemDesc": item.item_name,
            "Amount": round(gross_amount, 2),
            "Discount": round(discount, 2),
            "TaxAmt": round(tax, 2),
            "ItemTotal": round(item_total, 2),
            "TaxableValue": round(item_total - tax, 2),
            "TaxPercent": 15
        })

    # Calculate header tax amount based on items to ensure consistency
    header_tax_amt = round(total_item_tax, 2)
    
    payload = {
        "Header": {
            "CompCode": "AR01C00001",
            "OrgCode": "1010",
            "OrderType":  "OrderAPI",
            "SaleChannel": "SODAS ECOMM",
            "DocDate": str(get_datetime(doc.posting_date).date()),
            "ReferenceNo": reference_no,
            "RefOrderNo": doc.name,
            "CustomerName": doc.customer_name,
            "BillingStreet":   address.address_line2 if address and address.address_line2 else "",
            "BillingAddress1": address.address_line1 if address and address.address_line1 else "",
            "BillingZip": address.pincode if address and address.pincode else "",
            "BillingCountry": address.country if address and address.country else "",
            "ShippingName": doc.customer_name,
            "ShippingStreet": address.address_line2 if address and address.address_line2 else "",
            "ShippingAddress1": address.address_line1 if address and address.address_line1 else "",
            "ShippingZip": address.pincode if address and address.pincode else "",
            "ShippingCountry": address.country if address and address.country else "",
            "TaxMethod": "VAT-Inclusive",
            "ShippingMethod": "Standard",
            "ShippingStatus": "Pending",
            "PaymentMethod": "Prepaid",
            "PaymentStatus": "Paid" if doc.outstanding_amount == 0 else "Pending",
            "ItemsCount": len(doc.items),
            "TotalQty": abs(sum(item.qty for item in doc.items)),  # Positive total quantity
            "BasicAmt": round(basic_amt, 2),
            "Discount": round(total_discount, 2),
            "TaxAmt": header_tax_amt,
            "charges": abs(round(doc.total_taxes_and_charges, 2)),
            "SubTotal": round((basic_amt - total_discount) + abs(doc.total_taxes_and_charges), 2),
            "Total": abs(round(doc.grand_total, 2)),
            "Remarks": "Return" if doc.is_return == 1 else "Deliver ASAP",
            "User": "order_api_user"
        },
        "Items": items
    }

    return payload
# Helper Functions
def calculate_tax_amount(amount, discount):
    """Calculate tax amount with precise rounding"""
    net = amount - discount
    tax = net * 15 / 115
    return round(tax, 2)  # Round to 2 decimal places for halala precision

def calculate_discount(item_discount, global_discount):
    """Calculate total discount with precise rounding"""
    return round((item_discount or 0) + (global_discount or 0), 2)
# Manual Sync Endpoints
@frappe.whitelist()
def retry_failed_sync(doctype, docname):
    """Manual retry for failed syncs"""
    doc = frappe.get_doc(doctype, docname)
    
    if doctype == "Sales Order":
        enqueue_animo_order_sync(doc, None)
    elif doctype == "Sales Invoice":
        enqueue_animo_invoice_sync(doc, None)
    
    return f"Retry queued for {doctype} {docname}"