import frappe

@frappe.whitelist()
def getdocs():
    """
    Custom API to fetch metadata for specific DocTypes without 'message' wrapper.
    URL: /api/method/ichat.api.getdocs
    """
    # 1. Define your specific allowed doctypes
    allowed = ["Quality Inspection", "Quality Inspection Template", "Quality Inspection Parameter"]
    
    final_list = []

    for dt in allowed:
        # 2. Check if the user has permission to read this DocType
        if frappe.has_permission(dt, "read"):
            # 3. Fetch metadata from the DocType database table
            meta = frappe.get_value("DocType", dt, ["name", "module", "document_type"], as_dict=True)
            
            if meta:
                final_list.append({
                    "name": meta.name,
                    "module": meta.module,
                    "document_type": meta.document_type
                })

    # 4. Directly override the response object to remove the 'message' header
    frappe.response["data"] = final_list

@frappe.whitelist()
def get_doc_statuses():
    """
    Returns only the name and status label for all records in the allowed DocTypes.
    URL: /api/method/ichat.api.get_doc_statuses
    """
    allowed = ["Quality Inspection", "Quality Inspection Template", "Quality Inspection Parameter"]
    status_list = []

    for dt in allowed:
        if frappe.has_permission(dt, "read"):
            # Fetch only essential fields for speed
            records = frappe.get_all(dt, fields=["name", "docstatus"])
            
            for r in records:
                status_list.append({
                    "name": r.name,
                    "status": "Draft" if r.docstatus == 0 else "Submitted" if r.docstatus == 1 else "Cancelled",
                    "type": dt
                })

    frappe.response["data"] = status_list