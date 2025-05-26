# Copyright (c) 2025, shreyas and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class JobCardParts(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		actual_qty: DF.Float
		amount: DF.Currency
		item_code: DF.Link
		item_name: DF.Data | None
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		part_type: DF.Literal["Original", "Aftermarket", "Reconditioned"]
		qty: DF.Float
		rate: DF.Currency
		supplier: DF.Link | None
		warehouse: DF.Link | None
		warranty_months: DF.Int
	# end: auto-generated types
	pass
