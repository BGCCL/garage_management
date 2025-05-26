# Copyright (c) 2025, shreyas and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class JobCardService(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		actual_time: DF.Float
		estimated_time: DF.Float
		labor_rate: DF.Currency
		notes: DF.Text | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		service_category: DF.Literal["Engine", "Brakes", "Suspension", "Electrical", "Transmission", "AC", "Body Work", "Tires", "Oil Change", "General Maintenance", "Full"]
		service_description: DF.TextEditor
		service_item: DF.Link
		status: DF.Literal["Pending", "In Progress", "Completed", "Skipped"]
		technician: DF.Link | None
		total_labor_cost: DF.Currency
	# end: auto-generated types
	pass
