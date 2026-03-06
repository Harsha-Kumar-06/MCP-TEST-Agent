"""
HR Tools - Functions for HR-related operations.

These are mock implementations demonstrating the tool pattern.
In production, these would connect to your HRIS system.
"""

import re
from datetime import datetime, timedelta
from typing import Optional


def parse_flexible_date(date_str: str) -> str:
    """
    Parse a date string in various formats and return YYYY-MM-DD format.
    
    Supported formats:
    - MM/DD/YYYY or M/D/YYYY (e.g., "3/5/2026", "03/05/2026")
    - YYYY-MM-DD (e.g., "2026-03-05")
    - Month DD, YYYY (e.g., "March 5, 2026", "Mar 5, 2026")
    - DD Month YYYY (e.g., "5 March 2026")
    
    Args:
        date_str: Date string in any supported format
    
    Returns:
        str: Date in YYYY-MM-DD format, or original string if parsing fails
    """
    date_str = date_str.strip()
    
    # Month name mapping
    month_names = {
        'jan': 1, 'january': 1,
        'feb': 2, 'february': 2,
        'mar': 3, 'march': 3,
        'apr': 4, 'april': 4,
        'may': 5,
        'jun': 6, 'june': 6,
        'jul': 7, 'july': 7,
        'aug': 8, 'august': 8,
        'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10,
        'nov': 11, 'november': 11,
        'dec': 12, 'december': 12
    }
    
    # Try YYYY-MM-DD format first (already correct format)
    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
        try:
            parts = date_str.split('-')
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            datetime(year, month, day)  # Validate
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            pass
    
    # Try MM/DD/YYYY or M/D/YYYY format
    match_mdy = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_str)
    if match_mdy:
        try:
            month, day, year = int(match_mdy.group(1)), int(match_mdy.group(2)), int(match_mdy.group(3))
            datetime(year, month, day)  # Validate
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            pass
    
    # Try "Month DD, YYYY" or "Month DD YYYY" format
    match_month_text = re.match(r'^([a-zA-Z]+)\.?\s+(\d{1,2}),?\s*(\d{4})$', date_str)
    if match_month_text:
        try:
            month_str = match_month_text.group(1).lower()
            day = int(match_month_text.group(2))
            year = int(match_month_text.group(3))
            month = month_names.get(month_str)
            if month:
                datetime(year, month, day)  # Validate
                return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            pass
    
    # Try "DD Month YYYY" format
    match_day_month = re.match(r'^(\d{1,2})\s+([a-zA-Z]+)\.?\s*,?\s*(\d{4})$', date_str)
    if match_day_month:
        try:
            day = int(match_day_month.group(1))
            month_str = match_day_month.group(2).lower()
            year = int(match_day_month.group(3))
            month = month_names.get(month_str)
            if month:
                datetime(year, month, day)  # Validate
                return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            pass
    
    # If no pattern matches, return original (let the caller handle invalid input)
    return date_str


def submit_pto_request(
    employee_id: str,
    start_date: str,
    end_date: str,
    leave_type: str = "PTO",
    reason: Optional[str] = None
) -> dict:
    """
    Submit a PTO or leave request for an employee.
    
    Args:
        employee_id: The employee's ID number
        start_date: Start date of leave (flexible formats: YYYY-MM-DD, MM/DD/YYYY, "March 5, 2026", etc.)
        end_date: End date of leave (flexible formats: YYYY-MM-DD, MM/DD/YYYY, "March 5, 2026", etc.)
        leave_type: Type of leave (PTO, Sick, Personal, Vacation)
        reason: Optional reason for the leave request
    
    Returns:
        dict: Request confirmation with ticket number and status
    """
    # Parse dates to standard format
    parsed_start = parse_flexible_date(start_date)
    parsed_end = parse_flexible_date(end_date)
    
    # Validate dates
    try:
        start_dt = datetime.strptime(parsed_start, "%Y-%m-%d")
        end_dt = datetime.strptime(parsed_end, "%Y-%m-%d")
        
        if end_dt < start_dt:
            return {
                "status": "error",
                "message": f"End date ({parsed_end}) cannot be before start date ({parsed_start})"
            }
    except ValueError as e:
        return {
            "status": "error",
            "message": f"Invalid date format. Please use formats like 'YYYY-MM-DD', 'MM/DD/YYYY', or 'March 5, 2026'. Error: {e}"
        }
    
    # Mock implementation
    request_id = f"PTO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "status": "submitted",
        "request_id": request_id,
        "employee_id": employee_id,
        "leave_type": leave_type,
        "start_date": parsed_start,
        "end_date": parsed_end,
        "message": f"PTO request {request_id} submitted successfully. Your manager will be notified for approval.",
        "estimated_response": "Within 2 business days"
    }


def check_pto_balance(employee_id: str) -> dict:
    """
    Check the PTO balance for an employee.
    
    Args:
        employee_id: The employee's ID number
    
    Returns:
        dict: PTO balance information
    """
    # Mock implementation - return sample data
    return {
        "employee_id": employee_id,
        "pto_balance": {
            "available_days": 15,
            "used_days": 5,
            "pending_days": 2,
            "rollover_days": 3,
            "total_annual_days": 20
        },
        "sick_leave": {
            "available_days": 8,
            "used_days": 2,
            "total_annual_days": 10
        },
        "as_of_date": datetime.now().strftime("%Y-%m-%d")
    }


def get_benefits_info(benefit_type: str) -> dict:
    """
    Get information about company benefits.
    
    Args:
        benefit_type: Type of benefit (health, dental, vision, 401k, wellness, all)
    
    Returns:
        dict: Benefits information
    """
    benefits_data = {
        "health": {
            "name": "Health Insurance",
            "provider": "BlueCross BlueShield",
            "plans": ["Standard PPO", "High Deductible HSA"],
            "enrollment_period": "November 1-30",
            "contact": "benefits@company.com"
        },
        "dental": {
            "name": "Dental Insurance",
            "provider": "Delta Dental",
            "coverage": "Preventive 100%, Basic 80%, Major 50%",
            "annual_max": "$2,000"
        },
        "vision": {
            "name": "Vision Insurance",
            "provider": "VSP",
            "coverage": "Annual exam, $150 frame allowance",
            "contact": "benefits@company.com"
        },
        "401k": {
            "name": "401(k) Retirement Plan",
            "provider": "Fidelity",
            "company_match": "100% up to 4% of salary",
            "vesting": "Immediate vesting",
            "contribution_limit": "$23,000 (2024)"
        },
        "wellness": {
            "name": "Wellness Program",
            "benefits": ["Gym membership subsidy", "Mental health resources", "Health screenings"],
            "gym_subsidy": "$50/month",
            "eap_provider": "LifeWorks"
        }
    }
    
    if benefit_type.lower() == "all":
        return {"benefits": benefits_data}
    
    return benefits_data.get(benefit_type.lower(), {
        "error": f"Benefit type '{benefit_type}' not found. Available types: health, dental, vision, 401k, wellness"
    })


def get_payroll_info(employee_id: str, info_type: str) -> dict:
    """
    Get payroll-related information for an employee.
    
    Args:
        employee_id: The employee's ID number
        info_type: Type of info (summary, tax_forms, deductions, schedule)
    
    Returns:
        dict: Payroll information
    """
    payroll_data = {
        "summary": {
            "pay_frequency": "Bi-weekly",
            "next_pay_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "direct_deposit": "Enabled",
            "last_pay_stub": "Available in employee portal"
        },
        "tax_forms": {
            "w2_status": "Available for download in employee portal",
            "w4_last_updated": "2024-01-15",
            "state_forms": "Available in employee portal"
        },
        "deductions": {
            "categories": ["Health Insurance", "401k", "Dental", "Vision", "HSA"],
            "details": "View detailed breakdown in employee portal"
        },
        "schedule": {
            "pay_dates_2024": "1st and 15th of each month",
            "holiday_adjustments": "Pay dates falling on holidays are moved to prior business day"
        }
    }
    
    return {
        "employee_id": employee_id,
        "info_type": info_type,
        "data": payroll_data.get(info_type, payroll_data["summary"]),
        "note": "For detailed information, please access the employee self-service portal."
    }


def get_company_policy(policy_topic: str) -> dict:
    """
    Look up company policies on a specific topic.
    
    Args:
        policy_topic: Topic to look up (remote_work, dress_code, expenses, travel, conduct)
    
    Returns:
        dict: Policy information
    """
    policies = {
        "remote_work": {
            "title": "Remote Work Policy",
            "summary": "Hybrid work model: 3 days in office, 2 days remote",
            "eligibility": "All full-time employees after 90-day probation",
            "equipment": "Company provides laptop and necessary peripherals",
            "document": "HR-POL-2024-001"
        },
        "dress_code": {
            "title": "Dress Code Policy",
            "summary": "Business casual for office days, smart casual for client meetings",
            "guidelines": ["No jeans with holes", "Closed-toe shoes preferred", "Company branded wear encouraged"],
            "document": "HR-POL-2024-002"
        },
        "expenses": {
            "title": "Expense Reimbursement Policy",
            "summary": "Submit expenses within 30 days via Concur",
            "approval_limits": {"manager": 500, "director": 2000, "vp": 10000},
            "categories": ["Travel", "Meals", "Office Supplies", "Training"],
            "document": "FIN-POL-2024-001"
        },
        "travel": {
            "title": "Business Travel Policy",
            "summary": "Book via corporate travel portal, economy class for flights under 6 hours",
            "per_diem": {"domestic": 75, "international": 100},
            "document": "FIN-POL-2024-002"
        },
        "conduct": {
            "title": "Code of Conduct",
            "summary": "Professional behavior, respect, integrity, compliance",
            "reporting": "Ethics hotline: 1-800-XXX-XXXX",
            "document": "HR-POL-2024-003"
        }
    }
    
    if policy_topic.lower() in policies:
        return {
            "found": True,
            "policy": policies[policy_topic.lower()],
            "full_document": "Available in the company HR portal"
        }
    
    return {
        "found": False,
        "message": f"Policy on '{policy_topic}' not found in quick reference.",
        "available_topics": list(policies.keys()),
        "suggestion": "For other policies, please check the HR portal or contact HR directly."
    }
