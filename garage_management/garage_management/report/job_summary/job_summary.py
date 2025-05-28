import frappe
from frappe import _
from frappe.utils import flt, getdate, today, add_days, now_datetime, date_diff

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data)
    summary = get_summary_data(data)
    
    return columns, data, None, chart, summary

def get_columns():
    return [
        {
            "label": _("Job Card ID"),
            "fieldname": "job_card_id",
            "fieldtype": "Link",
            "options": "Garage Job Card",
            "width": 120
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 100
        },
        {
            "label": _("Priority"),
            "fieldname": "priority",
            "fieldtype": "Data",
            "width": 80
        },
        {
            "label": _("Job Date"),
            "fieldname": "job_date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Vehicle"),
            "fieldname": "vehicle_registration",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Customer"),
            "fieldname": "customer_name",
            "fieldtype": "Link",
            "width": 150,
            "options": "Customer"
        },
        {
            "label": _("Service Type"),
            "fieldname": "service_type",
            "fieldtype": "Data",
            "width": 120
        },
        {
            "label": _("Technician"),
            "fieldname": "technician_name",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 120
        },
        {
            "label": _("Estimated Hours"),
            "fieldname": "estimated_hours",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Actual Hours"),
            "fieldname": "actual_hours",
            "fieldtype": "Float",
            "width": 100
        },
        {
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "label": _("Expected Completion"),
            "fieldname": "expected_completion_date",
            "fieldtype": "Datetime",
            "width": 150
        },
        {
            "label": _("Days Overdue"),
            "fieldname": "days_overdue",
            "fieldtype": "Int",
            "width": 100
        }
    ]

def get_data(filters):
    # Build filter conditions
    filter_conditions = [
        ["docstatus", "!=", 2]  # Exclude cancelled documents
    ]
    
    if filters.get("status"):
        filter_conditions.append(["status", "=", filters.get("status")])
    
    if filters.get("priority"):
        filter_conditions.append(["priority", "=", filters.get("priority")])
    
    if filters.get("from_date"):
        filter_conditions.append(["job_date", ">=", filters.get("from_date")])
    
    if filters.get("to_date"):
        filter_conditions.append(["job_date", "<=", filters.get("to_date")])
    
    if filters.get("technician"):
        filter_conditions.append(["assigned_technician", "=", filters.get("technician")])
    
    if filters.get("vehicle"):
        filter_conditions.append(["vehicle", "=", filters.get("vehicle")])
    
    if filters.get("customer"):
        filter_conditions.append(["customer", "=", filters.get("customer")])
    
    
    # Fetch data using frappe.get_all
    fields = [
        "name as job_card_id",
        "status",
        "priority", 
        "job_date",
        "vehicle_registration",
        "customer_name",
        "service_type",
        "technician_name",
        "estimated_hours",	
        "actual_hours",
        "total_amount",
        "expected_completion_date"
    ]
    
    job_cards = frappe.get_all(
        "Garage Job Card",
        filters=filter_conditions,
        fields=fields,
        order_by="job_date desc, priority desc"
    )
    
    # Calculate days overdue for each job card
    current_datetime = now_datetime()
    
    for job_card in job_cards:
        days_overdue = 0
        
        if (job_card.get('status') in ['In Progress', 'Confirmed'] and 
            job_card.get('expected_completion_date')):
            
            expected_date = job_card.get('expected_completion_date')
            if expected_date < current_datetime:
                days_overdue = date_diff(current_datetime.date(), expected_date.date())
        
        job_card['days_overdue'] = days_overdue
    
    return job_cards

def get_chart_data(data):
    if not data:
        return None

    status_counts = {}
    
    for row in data:
        status = row.get('status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1

    # Define consistent color mapping per status
    status_color_map = {
        "Completed": "#28a745",      # Green
        "In Progress": "#ff9307",    # Yellow
        "Confirmed": "#17a2b8",      # Teal
        "Pending": "#6c757d",        # Grey
        "Cancelled": "#dc3545",      # Red
        "Unknown": "#7A7A7AFF"        
    }

    # Build labels and values using order from status_counts
    labels = list(status_counts.keys())
    values = [status_counts[status] for status in labels]
    colors = [status_color_map.get(status, "#C4C4C4") for status in labels]

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Job Cards by Status",
                    "values": values
                }
            ]
        },
        "type": "donut",
        "height": 300,
        "colors": colors
    }


def get_summary_data(data):
    
    if not data:
        return []
    
    total_jobs = len(data)
    completed_jobs = len([d for d in data if d.get('status') == 'Completed'])
    in_progress_jobs = len([d for d in data if d.get('status') == 'In Progress'])
    confirmed_jobs = len([d for d in data if d.get('status') == 'Confirmed'])
    overdue_jobs = len([d for d in data if flt(d.get('days_overdue', 0)) > 0])
    
    # Revenue calculations
    total_revenue = sum([flt(d.get('total_amount', 0)) for d in data])
    completed_revenue = sum([flt(d.get('total_amount', 0)) for d in data if d.get('status') == 'Completed'])
    
    # Time calculations
    avg_estimated_hours = 0
    avg_actual_hours = 0
    
    jobs_with_estimated_hours = [d for d in data if d.get('estimated_hours')]
    if jobs_with_estimated_hours:
        avg_estimated_hours = sum([flt(d.get('estimated_hours', 0)) for d in jobs_with_estimated_hours]) / len(jobs_with_estimated_hours)
    
    completed_jobs_with_hours = [d for d in data if d.get('actual_hours') and d.get('status') == 'Completed']
    if completed_jobs_with_hours:
        avg_actual_hours = sum([flt(d.get('actual_hours', 0)) for d in completed_jobs_with_hours]) / len(completed_jobs_with_hours)
    
    # Completion rate
    completion_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
    return [
        {
            "value": total_jobs,
            "label": _("Total Job Cards"),
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": completed_jobs,
            "label": _("Completed Jobs"),
            "datatype": "Int",
            "indicator": "Green"
        },
        {
            "value": round(completion_rate, 1),
            "label": _("Completion Rate %"),
            "datatype": "Percent",
            "indicator": "Green" if completion_rate >= 80 else "Red"
        },
        {
            "value": in_progress_jobs,
            "label": _("In Progress"),
            "datatype": "Int", 
            "indicator": "Orange"
        },
        {
            "value": confirmed_jobs,
            "label": _("Confirmed Jobs"),
            "datatype": "Int",
            "indicator": "Blue"
        },
        {
            "value": overdue_jobs,
            "label": _("Overdue Jobs"),
            "datatype": "Int",
            "indicator": "Red"
        },
        {
            "value": total_revenue,
            "label": _("Total Revenue"),
            "datatype": "Currency",
            "indicator": "Orange"
        },
        {
            "value": completed_revenue,
            "label": _("Completed Revenue"),
            "datatype": "Currency",
            "indicator": "Green"
        },
        {
            "value": round(avg_estimated_hours, 2),
            "label": _("Avg Estimated Hours"),
            "datatype": "Float",
            "indicator": "Blue"
        },
        {
            "value": round(avg_actual_hours, 2),
            "label": _("Avg Actual Hours"),
            "datatype": "Float",
            "indicator": "Blue" if avg_actual_hours <= avg_estimated_hours else "Red"
        }
    ]