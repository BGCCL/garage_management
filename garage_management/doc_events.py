import frappe

def sales_invoice_cancel(doc,methos):
    if doc.custom_garage_job_card:
        frappe.db.set_value("Garage Job Card",doc.custom_garage_job_card,"sales_invoice",None)