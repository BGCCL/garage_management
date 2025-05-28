# Copyright (c) 2025, shreyas and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class WhatsAppSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		app_id: DF.Data | None
		business_id: DF.Data | None
		enabled: DF.Check
		phone_id: DF.Data | None
		token: DF.Password | None
		url: DF.Data | None
		version: DF.Data | None
		webhook_verify_token: DF.Data | None
	# end: auto-generated types
	pass
