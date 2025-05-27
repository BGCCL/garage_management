# Copyright (c) 2025, shreyas and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime


class GarageJobCard(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from garage_management.garage_management.doctype.job_card_parts.job_card_parts import JobCardParts
		from garage_management.garage_management.doctype.job_card_service.job_card_service import JobCardService
		from garage_management.garage_management.doctype.photos.photos import Photos

		actual_completion_date: DF.Datetime | None
		actual_hours: DF.Float
		amended_from: DF.Link | None
		assigned_technician: DF.Link | None
		contact_number: DF.Data | None
		customer: DF.Link | None
		customer_complaint: DF.TextEditor | None
		customer_name: DF.Data | None
		discount_amount: DF.Currency
		email: DF.Data | None
		estimated_hours: DF.Float
		expected_completion_date: DF.Datetime | None
		fuel_level: DF.Literal["Empty", "1/4 Tank", "1/2 Tank", "3/4 Tank", "Full Tank"]
		initial_inspection_notes: DF.TextEditor | None
		internal_notes: DF.TextEditor | None
		job_card_id: DF.Data | None
		job_date: DF.Date
		naming_series: DF.Literal["JOB-.YYYY.-.#####"]
		next_service_recommendation: DF.Text | None
		odometer_reading: DF.Int
		other_charges: DF.Currency
		parts_used: DF.Table[JobCardParts]
		photos_after: DF.Table[Photos]
		photos_before: DF.Table[Photos]
		priority: DF.Literal["Low", "Medium", "High", "Urgent"]
		quality_check_notes: DF.TextEditor | None
		sales_invoice: DF.Data | None
		service_advisor: DF.Link | None
		service_type: DF.Literal["Regular Maintenance", "Repair", "Inspection", "Warranty", "Accident Repair"]
		services: DF.Table[JobCardService]
		status: DF.Literal["Draft", "Confirmed", "In Progress", "Completed", "Cancelled"]
		technician_name: DF.Data | None
		total_amount: DF.Currency
		total_labor_cost: DF.Currency
		total_parts_cost: DF.Currency
		vehicle: DF.Link
		vehicle_make_model: DF.Data | None
		vehicle_registration: DF.Data | None
		warranty_period: DF.Int
		work_completed: DF.TextEditor | None
	# end: auto-generated types


	def validate(self):
		self.calculate_totals()
		self.validate_stock_availability()
	
	def on_submit(self):
		self.update_vehicle_service_info()
	
	def calculate_totals(self):
		total_labor = 0
		total_parts = 0
		total_hours = 0
		
		# Calculate labor costs
		for service in self.services:
			if service.actual_time and service.labor_rate:
				service.total_labor_cost = flt(service.actual_time) * flt(service.labor_rate)
				total_labor += service.total_labor_cost
				total_hours += flt(service.actual_time)
		
		# Calculate parts costs
		for part in self.parts_used:
			if part.qty and part.rate:
				part.amount = flt(part.qty) * flt(part.rate)
				total_parts += part.amount
		
		self.total_labor_cost = total_labor
		self.total_parts_cost = total_parts
		self.actual_hours = total_hours
		self.total_amount = total_labor + total_parts + flt(self.other_charges) - flt(self.discount_amount)
	
	def validate_stock_availability(self):
		for part in self.parts_used:
			if part.item_code and part.warehouse:
				available_qty = frappe.db.get_value("Bin", 
					{"item_code": part.item_code, "warehouse": part.warehouse}, "actual_qty") or 0
				
				if flt(part.qty) > flt(available_qty):
					frappe.throw(f"Insufficient stock for {part.item_code}. Available: {available_qty}, Required: {part.qty}")
	
	def update_vehicle_service_info(self):
		if self.status == "Completed":
			# Update vehicle's last service date and odometer reading
			frappe.db.set_value("Vehicle", self.vehicle, {
				"custom_last_service_date": self.actual_completion_date or now_datetime(),
				"custom_current_odometer_reading": self.odometer_reading
			})
	
	def create_stock_entry_on_completion(self):
		if self.status == "Completed" and self.parts_used:
			stock_entry = frappe.new_doc("Stock Entry")
			stock_entry.stock_entry_type = "Material Issue"
			stock_entry.purpose = "Material Issue"
			stock_entry.reference_doctype = "Garage Job Card"
			stock_entry.reference_docname = self.name
			
			for part in self.parts_used:
				stock_entry.append("items", {
					"item_code": part.item_code,
					"qty": part.qty,
					"s_warehouse": part.warehouse,
					"basic_rate": part.rate
				})
			
			stock_entry.save()
			stock_entry.submit()
			
			frappe.msgprint(f"Stock Entry {stock_entry.name} created for parts consumption")

@frappe.whitelist()
def create_sales_invoice(job_card):
    job_card_doc = frappe.get_doc("Garage Job Card", job_card)
    
    if job_card_doc.sales_invoice:
        frappe.throw("Sales Invoice already created for this Job Card")
    
    if job_card_doc.status != "Completed":
        frappe.throw("Cannot create invoice for incomplete job card")
    
    # Create Sales Invoice
    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = job_card_doc.customer
    invoice.posting_date = frappe.utils.today()
    invoice.custom_garage_job_card = job_card_doc.name
    invoice.due_date = frappe.utils.add_days(frappe.utils.today(), 30)  # 30 days payment terms
    invoice.update_stock = 1
    
    # Set customer details
    invoice.customer_name = job_card_doc.customer_name
    
    
    # Add labor charges as service items
    for service in job_card_doc.services:
        if service.total_labor_cost > 0:
            
            invoice.append("items", {
                "item_code": service.service_item,
                "item_name": f"Labor - {service.service_description}",
                "description": f"Service: {service.service_description}\nCategory: {service.service_category}\nTime: {service.actual_time} hours\nTechnician: {service.technician}",
                "qty": 1,
                "uom": "Nos",
                "rate": service.total_labor_cost,
                "amount": service.total_labor_cost,
            })
    
    # Add parts/items used
    for part in job_card_doc.parts_used:
        if part.amount > 0:
            invoice.append("items", {
                "item_code": part.item_code,
                "item_name": part.item_name,
                "description": f"Part used for vehicle service\nVehicle: {job_card_doc.vehicle_registration}\nWarranty: {part.warranty_months} months" if part.warranty_months else f"Part used for vehicle service\nVehicle: {job_card_doc.vehicle_registration}",
                "qty": part.qty,
                "uom": frappe.db.get_value("Item", part.item_code, "stock_uom") or "Nos",
                "rate": part.rate,
                "amount": part.amount,
                "warehouse": part.warehouse
            })
    
    # Add other charges if any
    if job_card_doc.other_charges > 0:
        other_charges_item = get_or_create_other_charges_item()
        invoice.append("items", {
            "item_code": other_charges_item,
            "item_name": "Other Charges",
            "description": "Additional charges for vehicle service",
            "qty": 1,
            "uom": "Nos",
            "rate": job_card_doc.other_charges,
            "amount": job_card_doc.other_charges
        })
    
    # Apply discount if any
    invoice.taxes_and_charges = frappe.db.get_value("Sales Taxes and Charges Template",filters={"title":"Tanzania Tax","company":frappe.defaults.get_user_default("Company")}, fieldname="name")
    if job_card_doc.discount_amount > 0:
        invoice.discount_amount = job_card_doc.discount_amount
        invoice.apply_discount_on = "Net Total"
    
    # Set additional invoice details
    invoice.remarks = f"Invoice for vehicle service - Job Card: {job_card_doc.name}\nVehicle: {job_card_doc.vehicle_registration} ({job_card_doc.vehicle_make_model})\nService Date: {job_card_doc.job_date}"
    
    # Calculate taxes (if applicable)
    invoice.calculate_taxes_and_totals()
    
    try:
        # Save the invoice
        print(invoice.base_grand_total)
        invoice.flags.ignore_permissions = True  # Ignore permissions for automated creation
        # invoice.flags.ignore_validate = True  # Ignore validation for automated creation
        invoice.save()
        
        # Update job card with invoice reference
        frappe.db.set_value("Garage Job Card", job_card_doc.name, "sales_invoice", invoice.name)
        
        return invoice.name
        
    except Exception as e:
        frappe.throw(f"Error creating Sales Invoice: {str(e)}")


def get_or_create_other_charges_item():
    """Get or create other charges item"""
    item_code = "OTHER-CHARGES"
    
    if not frappe.db.exists("Item", item_code):
        item = frappe.new_doc("Item")
        item.item_code = item_code
        item.item_name = "Other Charges"
        item.item_group = "Services"
        item.is_stock_item = 0
        item.is_sales_item = 1
        item.is_service_item = 1
        item.stock_uom = "Nos"
        item.description = "Miscellaneous charges for vehicle services"
        item.save()
    
    return item_code

def get_labor_income_account():
    """Get income account for labor charges"""
    # You can customize this based on your chart of accounts
    company = frappe.defaults.get_user_default("Company")
    
    # Try to get specific labor income account
    labor_account = frappe.db.get_value("Account", 
        {"account_name": "Service Income", "company": company, "is_group": 0}, "name")
    
    if not labor_account:
        # Fallback to default income account
        labor_account = frappe.db.get_value("Account", 
            {"account_type": "Income Account", "company": company, "is_group": 0}, "name")
    
    return labor_account

def get_parts_income_account():
    """Get income account for parts sales"""
    company = frappe.defaults.get_user_default("Company")
    
    # Try to get specific parts income account
    parts_account = frappe.db.get_value("Account", 
        {"account_name": "Sales", "company": company, "is_group": 0}, "name")
    
    if not parts_account:
        # Fallback to default income account
        parts_account = frappe.db.get_value("Account", 
            {"account_type": "Income Account", "company": company, "is_group": 0}, "name")
    
    return parts_account

def get_other_charges_income_account():
    """Get income account for other charges"""
    company = frappe.defaults.get_user_default("Company")
    
    # Try to get specific other income account
    other_account = frappe.db.get_value("Account", 
        {"account_name": "Other Income", "company": company, "is_group": 0}, "name")
    
    if not other_account:
        # Fallback to default income account
        other_account = frappe.db.get_value("Account", 
            {"account_type": "Income Account", "company": company, "is_group": 0}, "name")
    
    return other_account

def get_default_cost_center():
    """Get default cost center"""
    company = frappe.defaults.get_user_default("Company")
    
    # Get default cost center for the company
    cost_center = frappe.db.get_value("Cost Center", 
        {"company": company, "is_group": 0}, "name")
    
    if not cost_center:
        # Create a default cost center if it doesn't exist
        cost_center_doc = frappe.new_doc("Cost Center")
        cost_center_doc.cost_center_name = "Main"
        cost_center_doc.company = company
        cost_center_doc.parent_cost_center = company  # Company is usually the root cost center
        cost_center_doc.save()
        cost_center = cost_center_doc.name
    
    return cost_center

@frappe.whitelist()
def get_job_card_summary(job_card):
    """Get summary of job card for invoice preview"""
    job_card_doc = frappe.get_doc("Garage Job Card", job_card)
    
    summary = {
        "job_card": job_card_doc.name,
        "vehicle": job_card_doc.vehicle_registration,
        "customer": job_card_doc.customer_name,
        "total_labor_cost": job_card_doc.total_labor_cost,
        "total_parts_cost": job_card_doc.total_parts_cost,
        "other_charges": job_card_doc.other_charges,
        "discount_amount": job_card_doc.discount_amount,
        "total_amount": job_card_doc.total_amount,
        "services": [],
        "parts": []
    }
    
    for service in job_card_doc.services:
        summary["services"].append({
            "description": service.service_description,
            "category": service.service_category,
            "hours": service.actual_time,
            "rate": service.labor_rate,
            "amount": service.total_labor_cost
        })
    
    for part in job_card_doc.parts_used:
        summary["parts"].append({
            "item_code": part.item_code,
            "item_name": part.item_name,
            "qty": part.qty,
            "rate": part.rate,
            "amount": part.amount
        })
    
    return summary
