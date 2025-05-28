// Copyright (c) 2025, shreyas and contributors
// For license information, please see license.txt

frappe.query_reports["Job Summary"] = {
    "filters": [
		{
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"), 
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 0
        },
		{
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },
		{
			"fieldname": "vehicle",
			"label": __("Vehicle"),
			"fieldtype": "Link",
			"options": "Vehicle",
		},
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": [
                "",
                "Draft",
                "Confirmed", 
                "In Progress",
                "Completed",
                "Cancelled"
            ],
            "default": ""
        },
        {
            "fieldname": "priority", 
            "label": __("Priority"),
            "fieldtype": "Select",
            "options": [
                "",
                "Low",
                "Medium",
                "High", 
                "Urgent"
            ],
            "default": ""
        },
        {
            "fieldname": "technician",
            "label": __("Technician"),
            "fieldtype": "Link",
            "options": "Employee"
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname == "status") {
            if (value === "Completed") {
                value = `<span style="color: #28a745; font-weight: bold;">${value}</span>`;
            } else if (value === "In Progress") {
                value = `<span style="color: #ffc107; font-weight: bold;">${value}</span>`;
            } else if (value === "Confirmed") {
                value = `<span style="color:rgb(23, 120, 184); font-weight: bold;">${value}</span>`;
            } else if (value === "Cancelled") {
                value = `<span style="color: #dc3545; font-weight: bold;">${value}</span>`;
            } else if (value === "Draft") {
                value = `<span style="color: #6c757d; font-weight: bold;">${value}</span>`;
            }
        }
        
        if (column.fieldname == "priority") {
            if (value === "Urgent") {
                value = `<span style="color: #dc3545; font-weight: bold;">${value}</span>`;
            } else if (value === "High") {
                value = `<span style="color: #fd7e14; font-weight: bold;">${value}</span>`;
            } else if (value === "Medium") {
                value = `<span style="color: #17a2b8;">${value}</span>`;
            } else if (value === "Low") {
                value = `<span style="color: #6c757d;">${value}</span>`;
            }
        }
        
        if (column.fieldname == "days_overdue" && data && parseFloat(data.days_overdue) > 0) {
            value = `<span style="color: #dc3545; font-weight: bold;">${value}</span>`;
        }

        return value;
    },

    "onload": function(report) {
        // Add custom buttons
        report.page.add_inner_button(__("Create New Job Card"), function() {
            frappe.new_doc("Garage Job Card");
        });
        
    },

    "tree": false,
    
    // Custom initial load
    "initial_depth": 1,
    
    // Add custom actions for rows
    get_datatable_options(options) {
        return Object.assign(options, {
            checkboxColumn: true,
            events: {
                onCheckRow: function(data) {
                    let checked_items = data.map(d => d[0]);
                    if (checked_items.length > 0) {
                        // Enable bulk actions
                        console.log("Selected job cards:", checked_items);
                    }
                }
            }
        });
    }
};


// Auto-refresh every 5 minutes for real-time updates
setInterval(function() {
    if (cur_report_wrapper && cur_report_wrapper.report && 
        cur_report_wrapper.report.report_name === "Job Summary") {
        cur_report_wrapper.report.refresh();
    }
}, 300000);
