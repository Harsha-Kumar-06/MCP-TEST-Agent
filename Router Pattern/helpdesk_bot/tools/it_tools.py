"""
IT Tools - Functions for IT support operations.

These are mock implementations demonstrating the tool pattern.
In production, these would connect to your ITSM/ticketing system.
"""

from datetime import datetime
from typing import Optional


def diagnose_hardware_issue(
    employee_id: str,
    device_type: str,
    issue_description: str,
    symptoms: str = ""
) -> dict:
    """
    Run diagnostics for hardware-related issues.
    
    Args:
        employee_id: The employee's ID number
        device_type: Type of device (laptop, desktop, monitor, peripheral)
        issue_description: Description of the issue
        symptoms: Comma-separated list of symptoms (e.g., "slow, overheating, not_starting")
    
    Returns:
        dict: Diagnostic results and recommendations
    """
    # Mock diagnostic logic
    symptoms_list = [s.strip() for s in symptoms.split(",") if s.strip()] if symptoms else []
    diagnostic_id = f"DIAG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    recommendations = []
    severity = "low"
    
    if "slow" in issue_description.lower() or "slow" in symptoms_list:
        recommendations.extend([
            "Restart the device",
            "Close unnecessary applications",
            "Check for pending Windows updates",
            "Clear temporary files"
        ])
        severity = "medium"
    
    if "overheating" in issue_description.lower() or "overheating" in symptoms_list:
        recommendations.extend([
            "Ensure ventilation is not blocked",
            "Use on a hard surface",
            "Consider a laptop cooling pad"
        ])
        severity = "medium"
    
    if "not_starting" in symptoms_list or "won't start" in issue_description.lower():
        recommendations.extend([
            "Check power connection",
            "Try a different power outlet",
            "Remove and reseat battery (if applicable)"
        ])
        severity = "high"
    
    if not recommendations:
        recommendations = ["Please provide more details for accurate diagnosis"]
    
    return {
        "diagnostic_id": diagnostic_id,
        "employee_id": employee_id,
        "device_type": device_type,
        "severity": severity,
        "immediate_recommendations": recommendations,
        "next_steps": "If issue persists after trying recommendations, a support ticket will be created.",
        "self_help_resources": "IT Knowledge Base: kb.company.com/hardware"
    }


def request_software_license(
    employee_id: str,
    software_name: str,
    business_justification: str,
    urgency: str = "normal"
) -> dict:
    """
    Submit a request for a software license.
    
    Args:
        employee_id: The employee's ID number
        software_name: Name of the software (e.g., Adobe Creative Cloud, AutoCAD)
        business_justification: Why the software is needed
        urgency: Request urgency (low, normal, high, critical)
    
    Returns:
        dict: Request status and expected timeline
    """
    request_id = f"SW-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Mock software catalog lookup
    software_catalog = {
        "adobe": {"approver": "manager", "cost": "enterprise_licensed", "sla": "3-5 business days"},
        "microsoft": {"approver": "auto", "cost": "enterprise_licensed", "sla": "1 business day"},
        "slack": {"approver": "auto", "cost": "enterprise_licensed", "sla": "immediate"},
        "zoom": {"approver": "auto", "cost": "enterprise_licensed", "sla": "immediate"},
    }
    
    software_key = software_name.lower().split()[0]
    software_info = software_catalog.get(software_key, {"approver": "it_manager", "cost": "to_be_determined", "sla": "5-7 business days"})
    
    timeline_map = {
        "critical": "1 business day",
        "high": "2 business days",
        "normal": software_info["sla"],
        "low": "7 business days"
    }
    
    return {
        "status": "submitted",
        "request_id": request_id,
        "software_name": software_name,
        "employee_id": employee_id,
        "requires_approval": software_info["approver"],
        "estimated_timeline": timeline_map.get(urgency, software_info["sla"]),
        "message": f"License request {request_id} submitted successfully.",
        "tracking": "Track status at: servicedesk.company.com/requests"
    }


def create_support_ticket(
    employee_id: str,
    category: str,
    subject: str,
    description: str,
    priority: str = "medium"
) -> dict:
    """
    Create an IT support ticket for complex issues.
    
    Args:
        employee_id: The employee's ID number
        category: Ticket category (hardware, software, network, access, security)
        subject: Brief subject line
        description: Detailed description of the issue
        priority: Ticket priority (low, medium, high, critical)
    
    Returns:
        dict: Ticket information and SLA details
    """
    ticket_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    sla_map = {
        "critical": {"response": "15 minutes", "resolution": "4 hours"},
        "high": {"response": "1 hour", "resolution": "8 hours"},
        "medium": {"response": "4 hours", "resolution": "24 hours"},
        "low": {"response": "8 hours", "resolution": "72 hours"}
    }
    
    return {
        "ticket_id": ticket_id,
        "status": "open",
        "category": category,
        "subject": subject,
        "priority": priority,
        "employee_id": employee_id,
        "sla": sla_map.get(priority, sla_map["medium"]),
        "message": f"Support ticket {ticket_id} created successfully.",
        "next_steps": "An IT technician will be assigned and will contact you within the SLA response time.",
        "tracking_url": f"servicedesk.company.com/tickets/{ticket_id}"
    }


def check_system_status(system_name: str) -> dict:
    """
    Check the status of company systems and services.
    
    Args:
        system_name: Optional specific system to check (email, vpn, erp, crm, all)
    
    Returns:
        dict: System status information
    """
    # Mock system status data
    systems = {
        "email": {"status": "operational", "last_incident": None},
        "vpn": {"status": "operational", "last_incident": None},
        "erp": {"status": "operational", "last_incident": "2024-01-15 - Brief outage"},
        "crm": {"status": "operational", "last_incident": None},
        "file_storage": {"status": "operational", "last_incident": None},
        "intranet": {"status": "degraded", "message": "Scheduled maintenance at 2 AM EST"},
        "video_conferencing": {"status": "operational", "last_incident": None}
    }
    
    if system_name and system_name.lower() != "all":
        system = systems.get(system_name.lower())
        if system:
            return {
                "system": system_name,
                "status": system["status"],
                "details": system,
                "status_page": "status.company.com"
            }
        return {
            "error": f"System '{system_name}' not found",
            "available_systems": list(systems.keys())
        }
    
    return {
        "overall_status": "operational",
        "systems": systems,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status_page": "status.company.com"
    }


def reset_password(
    employee_id: str,
    system: str = "active_directory"
) -> dict:
    """
    Initiate a password reset for an employee.
    
    Args:
        employee_id: The employee's ID number
        system: System for password reset (active_directory, email, vpn, specific_app)
    
    Returns:
        dict: Password reset instructions
    """
    reset_token = f"RST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    return {
        "status": "initiated",
        "reset_token": reset_token,
        "employee_id": employee_id,
        "system": system,
        "instructions": [
            "A password reset link has been sent to your registered email",
            "The link expires in 24 hours",
            "New password must meet complexity requirements",
            "After reset, you may need to re-authenticate on all devices"
        ],
        "complexity_requirements": {
            "min_length": 12,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_number": True,
            "require_special": True,
            "no_recent_passwords": 5
        },
        "help": "If you don't receive the email, contact IT at x1234"
    }


def request_access(
    employee_id: str,
    system_name: str,
    access_level: str,
    business_justification: str,
    duration: str = "permanent"
) -> dict:
    """
    Submit a system access request.
    
    Args:
        employee_id: The employee's ID number
        system_name: Name of the system to access
        access_level: Level of access needed (read, write, admin)
        business_justification: Why access is needed
        duration: Access duration (permanent, 30_days, 90_days, project_based)
    
    Returns:
        dict: Access request status and approval workflow
    """
    request_id = f"ACC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Mock approval workflow based on access level
    approval_workflow = {
        "read": ["manager"],
        "write": ["manager", "data_owner"],
        "admin": ["manager", "data_owner", "security_team"]
    }
    
    return {
        "status": "pending_approval",
        "request_id": request_id,
        "employee_id": employee_id,
        "system_name": system_name,
        "access_level": access_level,
        "duration": duration,
        "approval_chain": approval_workflow.get(access_level, ["manager"]),
        "estimated_timeline": "1-3 business days",
        "message": f"Access request {request_id} submitted. Pending approval from: {', '.join(approval_workflow.get(access_level, ['manager']))}",
        "tracking": "Track status at: accessmanagement.company.com/requests"
    }
