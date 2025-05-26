// Copyright (c) 2025, shreyas and contributors
// For license information, please see license.txt

frappe.ui.form.on('Garage Job Card', {
    refresh: function(frm) {
        // Custom buttons based on status
        if (frm.doc.docstatus === 1) {
            if (frm.doc.status === 'Completed' && !frm.doc.sales_invoice) {
                frm.add_custom_button(__('Create Invoice'), function() {
                    create_sales_invoice(frm);
                });
            }
            
            if (frm.doc.status !== 'Delivered') {
                frm.add_custom_button(__('Update Status'), function() {
                    show_status_dialog(frm);
                });
            }
        }
        frm.set_df_property("sales_invoice","field_type","Link")
        frm.set_df_property("sales_invoice","options","Link")
    },
    
    vehicle: function(frm) {
        if (frm.doc.vehicle) {
            // Fetch vehicle details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Vehicle',
                    name: frm.doc.vehicle
                },
                callback: function(r) {
                    if (r.message) {
                        let vehicle = r.message;
                        frm.set_value('vehicle_make_model', vehicle.make + ' ' + vehicle.model);
                    }
                }
            });
        }
    },
    
    validate: function(frm) {
        calculate_totals(frm);
    }
});

// Child table scripts
frappe.ui.form.on('Job Card Service', {
    actual_time: function(frm, cdt, cdn) {
        calculate_service_cost(frm, cdt, cdn);
        calculate_totals(frm);
    },
    
    labor_rate: function(frm, cdt, cdn) {
        calculate_service_cost(frm, cdt, cdn);
        calculate_totals(frm);
    }
});

frappe.ui.form.on('Job Card Parts', {
    qty: function(frm, cdt, cdn) {
        calculate_part_amount(frm, cdt, cdn);
        calculate_totals(frm);
    },
    
    rate: function(frm, cdt, cdn) {
        calculate_part_amount(frm, cdt, cdn);
        calculate_totals(frm);
    },
    
    item_code: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && row.warehouse) {
            // Get available quantity
            frappe.call({
                method: 'erpnext.stock.utils.get_stock_balance',
                args: {
                    item_code: row.item_code,
                    warehouse: row.warehouse
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'actual_qty', r.message);
                    }
                }
            });
        }
    }
});

// Helper functions
function calculate_service_cost(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let total_cost = (row.actual_time || 0) * (row.labor_rate || 0);
    frappe.model.set_value(cdt, cdn, 'total_labor_cost', total_cost);
}

function calculate_part_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    let amount = (row.qty || 0) * (row.rate || 0);
    frappe.model.set_value(cdt, cdn, 'amount', amount);
}

function calculate_totals(frm) {
    let total_labor = 0;
    let total_parts = 0;
    
    // Calculate labor cost
    frm.doc.services.forEach(function(row) {
        total_labor += row.total_labor_cost || 0;
    });
    
    // Calculate parts cost
    frm.doc.parts_used.forEach(function(row) {
        total_parts += row.amount || 0;
    });
    
    frm.set_value('total_labor_cost', total_labor);
    frm.set_value('total_parts_cost', total_parts);
    
    let total = total_labor + total_parts + (frm.doc.other_charges || 0) - (frm.doc.discount_amount || 0);
    frm.set_value('total_amount', total);
}

function create_sales_invoice(frm) {
    // Show preview dialog first
    frappe.call({
        method: 'garage_management.garage_management.doctype.garage_job_card.garage_job_card.get_job_card_summary',
        args: {
            job_card: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                show_invoice_preview(frm, r.message);
            }
        }
    });
}

function show_invoice_preview(frm, summary) {
    let d = new frappe.ui.Dialog({
        title: 'Invoice Preview',
        fields: [
            {
                fieldtype: 'HTML',
                options: `
                    <div class="invoice-preview">
                        <h4>Invoice Summary</h4>
                        <p><strong>Vehicle:</strong> ${summary.vehicle}</p>
                        <p><strong>Customer:</strong> ${summary.customer}</p>
                        <hr>
                        <p><strong>Labor Cost:</strong> ${format_currency(summary.total_labor_cost)}</p>
                        <p><strong>Parts Cost:</strong> ${format_currency(summary.total_parts_cost)}</p>
                        <p><strong>Other Charges:</strong> ${format_currency(summary.other_charges)}</p>
                        <p><strong>Discount:</strong> ${format_currency(summary.discount_amount)}</p>
                        <hr>
                        <p><strong>Total Amount:</strong> ${format_currency(summary.total_amount)}</p>
                    </div>
                `
            }
        ],
        primary_action_label: 'Create Invoice',
        primary_action(values) {
            frappe.call({
                method: 'garage_management.garage_management.doctype.garage_job_card.garage_job_card.create_sales_invoice',
                args: {
                    job_card: frm.doc.name
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.msgprint(__('Sales Invoice {0} created successfully', [r.message]));
                        frm.reload_doc();
                    }
                }
            });
            d.hide();
        }
    });
    d.show();
}

function show_status_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: 'Update Job Status',
        fields: [
            {
                label: 'Status',
                fieldname: 'status',
                fieldtype: 'Select',
                options: 'In Progress\nQuality Check\nCompleted\nDelivered',
                reqd: 1
            },
            {
                label: 'Notes',
                fieldname: 'notes',
                fieldtype: 'Text'
            }
        ],
        primary_action_label: 'Update',
        primary_action(values) {
            frm.set_value('status', values.status);
            if (values.status === 'Completed') {
                frm.set_value('actual_completion_date', frappe.datetime.now_datetime());
            }
            frm.save();
            d.hide();
        }
    });
    d.show();
}