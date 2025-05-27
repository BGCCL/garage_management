// Copyright (c) 2025, shreyas and contributors
// For license information, please see license.txt

frappe.ui.form.on('Garage Job Card', {
    before_workflow_action: function (frm) {
        check_mandatory_fields(frm)

    },
    refresh: function (frm) {
        // Custom buttons based on status
        if (frm.doc.docstatus === 1) {
            if (frm.doc.status === 'Completed' && !frm.doc.sales_invoice) {
                frm.add_custom_button(__('Create Invoice'), function () {
                    create_sales_invoice(frm);
                });
            }
            if (frm.doc.status !== 'Completed' || (frm.doc.status === 'Completed' && !frm.doc.sales_invoice)) {
                frm.dashboard.parent.hide();
            }
        }
    },
    vehicle: function (frm) {
        if (frm.doc.vehicle) {
            // Fetch vehicle details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Vehicle',
                    name: frm.doc.vehicle
                },
                callback: function (r) {
                    if (r.message) {
                        let vehicle = r.message;
                        frm.set_value('vehicle_make_model', vehicle.make + ' ' + vehicle.model);
                    }
                }
            });
        }
    },

    validate: function (frm) {
        calculate_totals(frm);
    }
});

// Child table scripts
frappe.ui.form.on('Job Card Service', {
    actual_time: function (frm, cdt, cdn) {
        calculate_service_cost(frm, cdt, cdn);
        calculate_totals(frm);
    },

    labor_rate: function (frm, cdt, cdn) {
        calculate_service_cost(frm, cdt, cdn);
        calculate_totals(frm);
    }
});

frappe.ui.form.on('Job Card Parts', {
    qty: function (frm, cdt, cdn) {
        calculate_part_amount(frm, cdt, cdn);
        calculate_totals(frm);
    },

    rate: function (frm, cdt, cdn) {
        calculate_part_amount(frm, cdt, cdn);
        calculate_totals(frm);
    },

    item_code: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item_code && row.warehouse) {
            // Get available quantity
            frappe.call({
                method: 'erpnext.stock.utils.get_stock_balance',
                args: {
                    item_code: row.item_code,
                    warehouse: row.warehouse
                },
                callback: function (r) {
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
    frm.doc.services.forEach(function (row) {
        total_labor += row.total_labor_cost || 0;
    });

    // Calculate parts cost
    frm.doc.parts_used.forEach(function (row) {
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
        callback: function (r) {
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
                    <div style="
                        font-family: 'Courier New', monospace;
                        border: 1px dashed #000;
                        padding: 15px;
                        width: 300px;
                        margin: 0 auto;
                        background-color: #fff;">
                        <h4 style="text-align: center; margin-bottom: 10px;">Sales Invoice</h4>
                        <hr style="border-top: 1px dashed #000;">
                        <p><strong>Vehicle:</strong> ${summary.vehicle}</p>
                        <p><strong>Customer:</strong> ${summary.customer}</p>
                        <hr style="border-top: 1px dashed #000;">

                        <p><strong>Labor Cost:</strong> ${format_currency(summary.total_labor_cost)}</p>
                        <p><strong>Parts Cost:</strong> ${format_currency(summary.total_parts_cost)}</p>
                        <p><strong>Other Charges:</strong> ${format_currency(summary.other_charges)}</p>
                        <p><strong>Discount:</strong> -${format_currency(summary.discount_amount)}</p>

                        <hr style="border-top: 1px dashed #000;">
                        <p style="font-size: 16px;"><strong>Total:</strong> ${format_currency(summary.total_amount)}</p>
                        <p style="text-align: right; font-size: 12px; margin-top: 4px;">(Excluding Tax)</p>
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
                callback: function (r) {
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
    console.clear()
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


function check_mandatory_fields(frm) {
    let has_errors = false;
    frm.scroll_set = false;

    if (frm.doc.docstatus === 2) return true; // don't check on cancel

    $.each(frappe.model.get_all_docs(frm.doc), function (i, doc) {
        let error_fields = [];
        let folded = false;

        $.each(frappe.meta.docfield_list[doc.doctype] || [], function (i, docfield) {
            if (docfield.fieldname) {
                const df = frappe.meta.get_docfield(doc.doctype, docfield.fieldname, doc.name);

                if (df.fieldtype === "Fold") folded = frm.layout.folded;

                if (is_mandatory(doc, df) && !frappe.model.has_value(doc.doctype, doc.name, df.fieldname)) {
                    has_errors = true;
                    error_fields.push(__(df.label, null, df.parent));
                    if (!frm.scroll_set) {
                        frm.scroll_to_field(doc.parentfield || df.fieldname);
                        frm.scroll_set = true;
                    }
                    if (folded) {
                        frm.layout.unfold();
                        folded = false;
                    }
                }
            }
        });

        if (error_fields.length) {
            let meta = frappe.get_meta(doc.doctype);
            let message = __("Mandatory fields required in {0}", [__(doc.doctype)]);
            message += "<br><br><ul><li>" + error_fields.join("</li><li>") + "</li></ul>";
            frappe.dom.unfreeze()
            frappe.throw({ title: __("Missing Fields"), message: message });

            frm.refresh();
        }
    });

    return !has_errors;
}

function is_mandatory(doc, df) {
    if (df.reqd) return true;
    if (!df.mandatory_depends_on || !doc) return false;

    const expression = df.mandatory_depends_on;
    let out;

    if (typeof expression === "boolean") {
        out = expression;
    } else if (typeof expression === "function") {
        out = expression(doc);
    } else if (expression.substr(0, 5) === "eval:") {
        try {
            out = frappe.utils.eval(expression.substr(5), { doc });
        } catch (e) {
            frappe.throw(__('Invalid "mandatory_depends_on" expression'));
        }
    } else {
        out = !!doc[expression];
    }

    return out;
}


const scroll_to = (fieldname) => {
    frm.scroll_to_field(fieldname);
    frm.scroll_set = true;
};