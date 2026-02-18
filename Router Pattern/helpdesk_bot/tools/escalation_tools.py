"""
Human Escalation Tools - Route conversations to human specialists.

Supports:
1. Live chat handoff
2. Callback scheduling
3. Ticket escalation with context
4. Expert finder
5. Microsoft Teams notifications
6. Email notifications
"""

import os
import json
import smtplib
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import specialist loader for dynamic specialist data
from .specialist_loader import load_specialists, get_specialist_by_email, get_available_specialists, clear_cache as clear_specialist_cache

# Optional imports - install as needed
try:
    import httpx  # For async HTTP requests (pip install httpx)
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests  # Fallback for sync requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ============================================================
# CONFIGURATION - Set these in your .env file
# ============================================================

# Application Base URL (for generating specialist chat URLs)
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8080")

# Microsoft Teams Webhook URLs (per department channel)
TEAMS_WEBHOOKS = {
    "IT_Support": os.getenv("TEAMS_WEBHOOK_IT", ""),
    "HR": os.getenv("TEAMS_WEBHOOK_HR", ""),
    "Sales": os.getenv("TEAMS_WEBHOOK_SALES", ""),
    "Legal": os.getenv("TEAMS_WEBHOOK_LEGAL", ""),
}

# Microsoft Graph API (for direct Teams messages)
GRAPH_CONFIG = {
    "tenant_id": os.getenv("AZURE_TENANT_ID", ""),
    "client_id": os.getenv("AZURE_CLIENT_ID", ""),
    "client_secret": os.getenv("AZURE_CLIENT_SECRET", ""),
}

# Email Configuration
EMAIL_CONFIG = {
    "smtp_server": os.getenv("SMTP_SERVER", "smtp.office365.com"),
    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
    "smtp_username": os.getenv("SMTP_USERNAME", ""),
    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
    "from_email": os.getenv("FROM_EMAIL", "helpdesk@company.com"),
    "from_name": os.getenv("FROM_NAME", "HelpDesk Bot"),
}

# Enable/disable real notifications (set to True when ready)
NOTIFICATIONS_ENABLED = os.getenv("ENABLE_NOTIFICATIONS", "false").lower() == "true"


# ============================================================
# SPECIALIST CHAT SESSION GENERATION
# ============================================================

import secrets

def generate_specialist_chat_session(
    escalation_id: str,
    department: str,
    urgency: str,
    issue_summary: str,
    employee_id: str,
    servicenow_incident: str = None,
) -> dict:
    """
    Generate a secure specialist chat session with unique URL.
    Registers the session with the FastAPI server for validation.
    
    Args:
        escalation_id: Unique escalation identifier
        department: Department (IT_Support, HR, Sales, Legal)
        urgency: Priority level
        issue_summary: Brief description of the issue
        employee_id: Requesting employee ID
        servicenow_incident: Optional ServiceNow ticket number
    
    Returns:
        dict: Contains specialist_url, specialist_token, and chat_url
    """
    # Generate secure token for specialist access
    specialist_token = secrets.token_urlsafe(32)
    
    # Generate URLs
    specialist_url = f"{APP_BASE_URL}/specialist?escalation_id={escalation_id}&token={specialist_token}"
    user_chat_url = f"{APP_BASE_URL}/escalation/{escalation_id}"
    
    # Register session with FastAPI server (non-blocking)
    session_data = {
        "escalation_id": escalation_id,
        "specialist_token": specialist_token,
        "department": department,
        "urgency": urgency,
        "issue_summary": issue_summary,
        "employee_id": employee_id,
        "servicenow_incident": servicenow_incident,
    }
    
    def register_session():
        """Background registration to avoid blocking."""
        import time
        time.sleep(0.5)  # Small delay to ensure main request completes first
        try:
            if REQUESTS_AVAILABLE:
                response = requests.post(
                    f"{APP_BASE_URL}/api/escalation/register",
                    json=session_data,
                    timeout=10
                )
                if response.status_code == 200:
                    print(f"Session registered: {escalation_id}")
                else:
                    print(f"Session registration warning: {response.status_code}")
        except Exception as e:
            print(f"Session registration error (non-fatal): {e}")
    
    # Run registration in background thread
    import threading
    thread = threading.Thread(target=register_session, daemon=True)
    thread.start()
    
    return {
        "escalation_id": escalation_id,
        "specialist_token": specialist_token,
        "specialist_url": specialist_url,
        "user_chat_url": user_chat_url,
        "created_at": datetime.now().isoformat(),
    }


# ============================================================
# SERVICENOW CONFIGURATION
# ============================================================

SERVICENOW_CONFIG = {
    "instance_url": os.getenv("SERVICENOW_INSTANCE", ""),  # e.g., https://yourcompany.service-now.com
    "username": os.getenv("SERVICENOW_USERNAME", ""),
    "password": os.getenv("SERVICENOW_PASSWORD", ""),
    "api_key": os.getenv("SERVICENOW_API_KEY", ""),  # Alternative to username/password
    "enabled": os.getenv("SERVICENOW_ENABLED", "false").lower() == "true",
    "default_caller": os.getenv("SNOW_DEFAULT_CALLER", "admin"),  # Default caller when unknown
}

# Map departments to ServiceNow assignment groups
SERVICENOW_ASSIGNMENT_GROUPS = {
    "IT_Support": os.getenv("SNOW_GROUP_IT", "IT Support"),
    "HR": os.getenv("SNOW_GROUP_HR", "Human Resources"),
    "Sales": os.getenv("SNOW_GROUP_SALES", "Sales Operations"),
    "Legal": os.getenv("SNOW_GROUP_LEGAL", "Legal"),
}

# Map urgency levels to ServiceNow impact/urgency values
SERVICENOW_URGENCY_MAP = {
    "critical": {"impact": "1", "urgency": "1", "priority": "1"},  # Critical
    "high": {"impact": "2", "urgency": "1", "priority": "2"},      # High
    "normal": {"impact": "2", "urgency": "2", "priority": "3"},    # Moderate
    "low": {"impact": "3", "urgency": "3", "priority": "4"},       # Low
}

# ServiceNow category mappings
SERVICENOW_CATEGORIES = {
    "IT_Support": {"category": "Hardware", "subcategory": "Laptop"},
    "HR": {"category": "Human Resources", "subcategory": "General Inquiry"},
    "Sales": {"category": "Sales", "subcategory": "Customer Request"},
    "Legal": {"category": "Legal", "subcategory": "Contract Review"},
}


# ============================================================
# Specialist Directory - Loaded from configured source
# ============================================================
# Source configured via SPECIALIST_SOURCE environment variable:
#   - static: Hardcoded fallback (default)
#   - csv: Load from data/specialists.csv
#   - json: Load from data/specialists.json
#   - database: Load from SQLite or PostgreSQL
#   - servicenow: Load from ServiceNow assignment groups
#   - ldap: Load from Active Directory/LDAP
# ============================================================

def get_specialists() -> dict:
    """
    Get all specialists from the configured source.
    Results are cached for SPECIALISTS_CACHE_TTL minutes.
    """
    return load_specialists()


# For backward compatibility, SPECIALISTS is a property-like dict
# that loads dynamically from the configured source
class _SpecialistsProxy(dict):
    """Proxy dict that loads specialists on demand."""
    
    def __getitem__(self, key):
        return load_specialists().get(key, [])
    
    def get(self, key, default=None):
        return load_specialists().get(key, default)
    
    def keys(self):
        return load_specialists().keys()
    
    def values(self):
        return load_specialists().values()
    
    def items(self):
        return load_specialists().items()
    
    def __iter__(self):
        return iter(load_specialists())
    
    def __len__(self):
        return len(load_specialists())


SPECIALISTS = _SpecialistsProxy()


# ============================================================
# NOTIFICATION HELPER FUNCTIONS
# ============================================================

def _send_teams_webhook(department: str, message_card: dict) -> dict:
    """
    Send a message to Teams channel via Incoming Webhook.
    
    This is the SIMPLEST method - no Azure AD app required.
    Just create an Incoming Webhook in your Teams channel.
    
    Args:
        department: Target department to get webhook URL
        message_card: Adaptive Card or MessageCard payload
    
    Returns:
        dict: Status of the notification
    """
    webhook_url = TEAMS_WEBHOOKS.get(department, "")
    
    if not webhook_url or not NOTIFICATIONS_ENABLED:
        return {"sent": False, "reason": "Webhook not configured or notifications disabled"}
    
    try:
        if REQUESTS_AVAILABLE:
            response = requests.post(
                webhook_url,
                json=message_card,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            return {
                "sent": response.status_code == 200,
                "status_code": response.status_code,
                "platform": "teams_webhook"
            }
        else:
            return {"sent": False, "reason": "requests library not installed"}
    except Exception as e:
        return {"sent": False, "error": str(e)}


def _create_teams_adaptive_card(
    escalation_id: str,
    department: str,
    employee_id: str,
    issue_summary: str,
    urgency: str,
    assigned_to: str = None,
    chat_url: str = None
) -> dict:
    """
    Create a rich Adaptive Card for Teams notification.
    
    This creates an interactive card with:
    - Issue details
    - Action buttons (Accept, View Chat, etc.)
    """
    urgency_colors = {
        "critical": "attention",
        "high": "warning", 
        "normal": "accent",
        "low": "good"
    }
    
    card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"🚨 New Escalation: {escalation_id}",
                            "weight": "bolder",
                            "size": "large",
                            "color": urgency_colors.get(urgency, "default")
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Department", "value": department},
                                {"title": "Urgency", "value": urgency.upper()},
                                {"title": "Employee", "value": employee_id},
                                {"title": "Assigned To", "value": assigned_to or "Unassigned"},
                                {"title": "Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M")}
                            ]
                        },
                        {
                            "type": "TextBlock",
                            "text": "**Issue Summary:**",
                            "weight": "bolder",
                            "spacing": "medium"
                        },
                        {
                            "type": "TextBlock",
                            "text": issue_summary,
                            "wrap": True
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "📋 View Full Details",
                            "url": f"https://helpdesk.company.com/escalation/{escalation_id}"
                        },
                        {
                            "type": "Action.OpenUrl",
                            "title": "💬 Join Chat",
                            "url": chat_url or f"https://chat.company.com/session/{escalation_id}"
                        }
                    ]
                }
            }
        ]
    }
    return card


def _send_email_notification(
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
    body_text: str = None
) -> dict:
    """
    Send an email notification via SMTP.
    
    Args:
        to_email: Recipient email address
        to_name: Recipient name
        subject: Email subject
        body_html: HTML body content
        body_text: Plain text body (optional fallback)
    
    Returns:
        dict: Status of email send
    """
    if not NOTIFICATIONS_ENABLED or not EMAIL_CONFIG["smtp_username"]:
        return {"sent": False, "reason": "Email not configured or notifications disabled"}
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{EMAIL_CONFIG['from_name']} <{EMAIL_CONFIG['from_email']}>"
        msg["To"] = f"{to_name} <{to_email}>"
        
        # Add plain text version
        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        
        # Add HTML version
        msg.attach(MIMEText(body_html, "html"))
        
        # Send via SMTP
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["smtp_username"], EMAIL_CONFIG["smtp_password"])
            server.sendmail(EMAIL_CONFIG["from_email"], to_email, msg.as_string())
        
        return {"sent": True, "to": to_email, "platform": "email"}
    
    except Exception as e:
        return {"sent": False, "error": str(e)}


def _create_escalation_email(
    escalation_id: str,
    department: str,
    employee_id: str,
    issue_summary: str,
    urgency: str,
    assigned_to: str = None,
    chat_url: str = None
) -> tuple:
    """
    Create HTML and plain text email content for escalation.
    
    Args:
        chat_url: Direct link to join the chat session (specialist URL with token)
    
    Returns:
        tuple: (subject, html_body, text_body)
    """
    subject = f"[{urgency.upper()}] New Escalation {escalation_id} - {department}"
    
    # Use the specialist chat URL if provided, otherwise fallback
    join_chat_url = chat_url or f"https://chat.company.com/session/{escalation_id}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; }}
            .header {{ background: #0078d4; color: white; padding: 20px; }}
            .content {{ padding: 20px; }}
            .urgency-critical {{ color: #d13438; font-weight: bold; }}
            .urgency-high {{ color: #ff8c00; font-weight: bold; }}
            .fact {{ margin: 8px 0; }}
            .label {{ color: #666; }}
            .btn {{ 
                display: inline-block; 
                padding: 10px 20px; 
                background: #0078d4; 
                color: white; 
                text-decoration: none;
                border-radius: 4px;
                margin: 5px;
            }}
            .btn-primary {{
                background: #107c10;
                font-size: 16px;
                padding: 12px 24px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>🚨 New Escalation Request</h2>
        </div>
        <div class="content">
            <div class="fact"><span class="label">Escalation ID:</span> <strong>{escalation_id}</strong></div>
            <div class="fact"><span class="label">Department:</span> {department}</div>
            <div class="fact"><span class="label">Urgency:</span> <span class="urgency-{urgency}">{urgency.upper()}</span></div>
            <div class="fact"><span class="label">Employee:</span> {employee_id}</div>
            <div class="fact"><span class="label">Assigned To:</span> {assigned_to or 'You'}</div>
            <div class="fact"><span class="label">Time:</span> {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            
            <h3>Issue Summary</h3>
            <p>{issue_summary}</p>
            
            <p style="margin-top: 20px;">
                <a class="btn btn-primary" href="{join_chat_url}">💬 Join Chat & Respond</a>
            </p>
            <p style="font-size: 12px; color: #666;">
                Click the button above to join the user's chat session and respond directly.
            </p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    NEW ESCALATION REQUEST
    ======================
    
    Escalation ID: {escalation_id}
    Department: {department}
    Urgency: {urgency.upper()}
    Employee: {employee_id}
    Assigned To: {assigned_to or 'You'}
    Time: {datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    Issue Summary:
    {issue_summary}
    
    JOIN CHAT & RESPOND:
    {join_chat_url}
    
    Click the link above to join the user's chat session and respond directly.
    """
    
    return subject, html_body, text_body


# ============================================================
# SERVICENOW API FUNCTIONS
# ============================================================

# Cache for assignment group sys_ids
_assignment_group_cache = {}

def _get_servicenow_auth():
    """Get authentication headers for ServiceNow API."""
    import base64
    
    if SERVICENOW_CONFIG["api_key"]:
        return {"Authorization": f"Bearer {SERVICENOW_CONFIG['api_key']}"}
    elif SERVICENOW_CONFIG["username"] and SERVICENOW_CONFIG["password"]:
        credentials = f"{SERVICENOW_CONFIG['username']}:{SERVICENOW_CONFIG['password']}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    return {}


def _get_assignment_group_sys_id(group_name: str) -> str:
    """
    Look up the sys_id for an assignment group by name.
    Results are cached to avoid repeated API calls.
    """
    if not group_name:
        return None
    
    # Check cache first
    if group_name in _assignment_group_cache:
        return _assignment_group_cache[group_name]
    
    if not SERVICENOW_CONFIG["enabled"] or not SERVICENOW_CONFIG["instance_url"]:
        return None
    
    try:
        url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/sys_user_group"
        params = {
            "sysparm_query": f"name={group_name}",
            "sysparm_fields": "sys_id,name",
            "sysparm_limit": 1
        }
        headers = {
            "Accept": "application/json",
            **_get_servicenow_auth()
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json().get("result", [])
            if results:
                sys_id = results[0].get("sys_id")
                _assignment_group_cache[group_name] = sys_id
                print(f"Found assignment group '{group_name}' with sys_id: {sys_id}")
                return sys_id
        
        print(f"Assignment group '{group_name}' not found in ServiceNow")
        return None
    except Exception as e:
        print(f"Error looking up assignment group: {e}")
        return None


def create_servicenow_incident(
    escalation_id: str,
    department: str,
    employee_id: str,
    issue_summary: str,
    urgency: str,
    assigned_to: str = None,
    caller_email: str = None
) -> dict:
    """
    Create an incident in ServiceNow.
    
    Args:
        escalation_id: Internal escalation ID for tracking
        department: Department (IT_Support, HR, Sales, Legal)
        employee_id: Employee ID or email of the requester
        issue_summary: Description of the issue
        urgency: Priority level (critical, high, normal, low)
        assigned_to: Optional specific assignee
        caller_email: Optional caller email for ServiceNow caller lookup
    
    Returns:
        dict: ServiceNow incident details or error
    """
    if not SERVICENOW_CONFIG["enabled"] or not SERVICENOW_CONFIG["instance_url"]:
        return {"created": False, "reason": "ServiceNow not configured or disabled"}
    
    if not REQUESTS_AVAILABLE:
        return {"created": False, "reason": "requests library not installed"}
    
    try:
        # Get urgency/priority mapping
        priority_map = SERVICENOW_URGENCY_MAP.get(urgency, SERVICENOW_URGENCY_MAP["normal"])
        category_map = SERVICENOW_CATEGORIES.get(department, {})
        assignment_group_name = SERVICENOW_ASSIGNMENT_GROUPS.get(department, "Service Desk")
        
        # Look up the assignment group sys_id
        assignment_group_sys_id = _get_assignment_group_sys_id(assignment_group_name)
        
        # Build incident payload
        incident_data = {
            "short_description": f"[{escalation_id}] {issue_summary[:100]}",
            "description": f"""
HelpDesk Bot Escalation
=======================
Escalation ID: {escalation_id}
Department: {department}
Employee: {employee_id}
Urgency: {urgency}
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Issue Description:
{issue_summary}

---
This incident was automatically created by HelpDesk Bot.
Chat URL: https://chat.company.com/session/{escalation_id}
            """.strip(),
            "impact": priority_map["impact"],
            "urgency": priority_map["urgency"],
            "priority": priority_map["priority"],
            "state": "2",  # 2 = In Progress (Active)
            "category": category_map.get("category", "Inquiry / Help"),
            "subcategory": category_map.get("subcategory", "General"),
            "contact_type": "Chat Bot",
            "correlation_id": escalation_id,  # Link to our escalation ID
        }
        
        # Add assignment group if found
        if assignment_group_sys_id:
            incident_data["assignment_group"] = assignment_group_sys_id
        
        # Add caller - use default if not provided or unknown
        effective_caller = caller_email if caller_email and caller_email.lower() != "unknown" else SERVICENOW_CONFIG["default_caller"]
        if effective_caller:
            incident_data["caller_id"] = effective_caller
        
        # Make API request to create incident
        api_url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/incident"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **_get_servicenow_auth()
        }
        
        response = requests.post(
            api_url,
            json=incident_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json().get("result", {})
            return {
                "created": True,
                "incident_number": result.get("number"),
                "sys_id": result.get("sys_id"),
                "state": result.get("state"),
                "assignment_group": assignment_group_name,
                "priority": priority_map["priority"],
                "servicenow_url": f"{SERVICENOW_CONFIG['instance_url']}/incident.do?sys_id={result.get('sys_id')}",
                "platform": "servicenow"
            }
        else:
            return {
                "created": False,
                "status_code": response.status_code,
                "error": response.text[:500]
            }
            
    except Exception as e:
        return {"created": False, "error": str(e)}


def update_servicenow_incident(
    incident_number: str = None,
    sys_id: str = None,
    update_data: dict = None
) -> dict:
    """
    Update an existing ServiceNow incident.
    
    Args:
        incident_number: Incident number (e.g., INC0012345) - will lookup sys_id
        sys_id: Direct sys_id of the incident
        update_data: Dictionary of fields to update
    
    Returns:
        dict: Update status
    """
    if not SERVICENOW_CONFIG["enabled"] or not SERVICENOW_CONFIG["instance_url"]:
        return {"updated": False, "reason": "ServiceNow not configured"}
    
    if not sys_id and not incident_number:
        return {"updated": False, "reason": "Either sys_id or incident_number required"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **_get_servicenow_auth()
        }
        
        # If we only have incident_number, look up the sys_id
        if not sys_id and incident_number:
            lookup_url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/incident?sysparm_query=number={incident_number}&sysparm_limit=1"
            lookup_response = requests.get(lookup_url, headers=headers, timeout=10)
            if lookup_response.status_code == 200:
                results = lookup_response.json().get("result", [])
                if results:
                    sys_id = results[0].get("sys_id")
                else:
                    return {"updated": False, "reason": f"Incident {incident_number} not found"}
        
        # Update the incident
        api_url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/incident/{sys_id}"
        response = requests.patch(
            api_url,
            json=update_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json().get("result", {})
            return {
                "updated": True,
                "incident_number": result.get("number"),
                "state": result.get("state"),
                "sys_id": sys_id
            }
        else:
            return {"updated": False, "status_code": response.status_code, "error": response.text[:200]}
            
    except Exception as e:
        return {"updated": False, "error": str(e)}


def get_servicenow_incident(
    incident_number: str = None,
    sys_id: str = None,
    correlation_id: str = None
) -> dict:
    """
    Get details of a ServiceNow incident.
    
    Args:
        incident_number: Incident number (e.g., INC0012345)
        sys_id: Direct sys_id
        correlation_id: Our escalation_id to lookup by
    
    Returns:
        dict: Incident details
    """
    if not SERVICENOW_CONFIG["enabled"] or not SERVICENOW_CONFIG["instance_url"]:
        return {"found": False, "reason": "ServiceNow not configured"}
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **_get_servicenow_auth()
        }
        
        # Build query based on what we have
        if sys_id:
            api_url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/incident/{sys_id}"
        elif incident_number:
            api_url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/incident?sysparm_query=number={incident_number}&sysparm_limit=1"
        elif correlation_id:
            api_url = f"{SERVICENOW_CONFIG['instance_url']}/api/now/table/incident?sysparm_query=correlation_id={correlation_id}&sysparm_limit=1"
        else:
            return {"found": False, "reason": "No identifier provided"}
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("result", data)
            if isinstance(result, list):
                result = result[0] if result else None
            
            if result:
                return {
                    "found": True,
                    "incident_number": result.get("number"),
                    "sys_id": result.get("sys_id"),
                    "state": result.get("state"),
                    "short_description": result.get("short_description"),
                    "assigned_to": result.get("assigned_to", {}).get("display_value") if isinstance(result.get("assigned_to"), dict) else result.get("assigned_to"),
                    "assignment_group": result.get("assignment_group", {}).get("display_value") if isinstance(result.get("assignment_group"), dict) else result.get("assignment_group"),
                    "priority": result.get("priority"),
                    "comments": result.get("comments"),
                    "work_notes": result.get("work_notes"),
                    "resolved_at": result.get("resolved_at"),
                    "resolution_code": result.get("resolution_code"),
                }
            else:
                return {"found": False, "reason": "Incident not found"}
        else:
            return {"found": False, "status_code": response.status_code}
            
    except Exception as e:
        return {"found": False, "error": str(e)}


def add_servicenow_comment(
    incident_number: str = None,
    sys_id: str = None,
    comment: str = "",
    is_work_note: bool = False
) -> dict:
    """
    Add a comment or work note to a ServiceNow incident.
    
    Args:
        incident_number: Incident number
        sys_id: Direct sys_id
        comment: The comment text to add
        is_work_note: True for work note (internal), False for customer-visible comment
    
    Returns:
        dict: Status of comment addition
    """
    field = "work_notes" if is_work_note else "comments"
    return update_servicenow_incident(
        incident_number=incident_number,
        sys_id=sys_id,
        update_data={field: comment}
    )


def close_servicenow_incident(
    incident_number: str = None,
    sys_id: str = None,
    resolution_notes: str = "",
    resolution_code: str = "Solved (Permanently)"
) -> dict:
    """
    Close/resolve a ServiceNow incident.
    
    Args:
        incident_number: Incident number
        sys_id: Direct sys_id
        resolution_notes: Resolution description
        resolution_code: Resolution code (default: Solved Permanently)
    
    Returns:
        dict: Status of closure
    """
    return update_servicenow_incident(
        incident_number=incident_number,
        sys_id=sys_id,
        update_data={
            "state": "6",  # Resolved
            "close_code": resolution_code,
            "close_notes": resolution_notes,
        }
    )


def _notify_specialist(
    specialist: dict,
    department: str,
    escalation_id: str,
    employee_id: str,
    issue_summary: str,
    urgency: str,
    specialist_url: str = None
) -> dict:
    """
    Send notifications to a specialist via Teams AND Email.
    
    Args:
        specialist: Specialist dict with name, email
        department: Department name
        escalation_id: Unique escalation ID
        employee_id: Requesting employee ID
        issue_summary: Issue description
        urgency: Priority level
        specialist_url: URL for specialist to join the chat session
    
    Returns:
        dict: Notification results for both channels
    """
    results = {"teams": None, "email": None}
    
    # 1. Send Teams notification (to channel)
    teams_card = _create_teams_adaptive_card(
        escalation_id=escalation_id,
        department=department,
        employee_id=employee_id,
        issue_summary=issue_summary,
        urgency=urgency,
        assigned_to=specialist["name"],
        chat_url=specialist_url
    )
    results["teams"] = _send_teams_webhook(department, teams_card)
    
    # 2. Send Email notification (direct to specialist)
    subject, html_body, text_body = _create_escalation_email(
        escalation_id=escalation_id,
        department=department,
        employee_id=employee_id,
        issue_summary=issue_summary,
        urgency=urgency,
        assigned_to=specialist["name"],
        chat_url=specialist_url
    )
    results["email"] = _send_email_notification(
        to_email=specialist["email"],
        to_name=specialist["name"],
        subject=subject,
        body_html=html_body,
        body_text=text_body
    )
    
    return results


def escalate_to_human(
    department: str,
    issue_summary: str,
    employee_id: str,
    urgency: str
) -> dict:
    """
    Escalate a conversation to a human specialist.
    
    Sends REAL notifications via:
    - Microsoft Teams (channel webhook with Adaptive Card)
    - Email (direct to assigned specialist)
    - ServiceNow (creates incident/ticket)
    
    Args:
        department: Target department (IT_Support, HR, Sales, Legal)
        issue_summary: Brief summary of the issue
        employee_id: The employee requesting escalation (use 'unknown' if not known)
        urgency: Priority level (low, normal, high, critical)
    
    Returns:
        dict: Escalation confirmation with assigned specialist
    """
    escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Find available specialist
    specialists = SPECIALISTS.get(department, [])
    available = [s for s in specialists if s["available"]]
    
    notification_results = {"teams": None, "email": None, "servicenow": None}
    servicenow_incident = None
    
    # ============================================================
    # CREATE SERVICENOW INCIDENT
    # ============================================================
    servicenow_result = create_servicenow_incident(
        escalation_id=escalation_id,
        department=department,
        employee_id=employee_id,
        issue_summary=issue_summary,
        urgency=urgency,
        assigned_to=available[0]["name"] if available else None,
        caller_email=employee_id
    )
    notification_results["servicenow"] = servicenow_result
    
    # Get ServiceNow incident number for reference
    if servicenow_result.get("created"):
        servicenow_incident = servicenow_result.get("incident_number")
    
    # ============================================================
    # GENERATE SPECIALIST CHAT SESSION URL
    # ============================================================
    chat_session = generate_specialist_chat_session(
        escalation_id=escalation_id,
        department=department,
        urgency=urgency,
        issue_summary=issue_summary,
        employee_id=employee_id,
        servicenow_incident=servicenow_incident
    )
    specialist_url = chat_session.get("specialist_url")
    
    if available:
        assigned = available[0]  # Simple assignment (enhance with load balancing)
        status = "assigned"
        message = f"Your request has been assigned to {assigned['name']}."
        response_time = "15-30 minutes" if urgency in ["high", "critical"] else "1-2 hours"
        
        # ============================================================
        # SEND REAL NOTIFICATIONS TO SPECIALIST
        # ============================================================
        specialist_notifications = _notify_specialist(
            specialist=assigned,
            department=department,
            escalation_id=escalation_id,
            employee_id=employee_id,
            issue_summary=issue_summary,
            urgency=urgency,
            specialist_url=specialist_url
        )
        notification_results["teams"] = specialist_notifications.get("teams")
        notification_results["email"] = specialist_notifications.get("email")
    else:
        assigned = None
        status = "queued"
        message = "All specialists are currently busy. You've been added to the queue."
        response_time = "2-4 hours"
        
        # Notify department channel even if no one available
        teams_card = _create_teams_adaptive_card(
            escalation_id=escalation_id,
            department=department,
            employee_id=employee_id,
            issue_summary=issue_summary,
            urgency=urgency,
            assigned_to="UNASSIGNED - Needs pickup",
            chat_url=specialist_url
        )
        notification_results["teams"] = _send_teams_webhook(department, teams_card)
    
    return {
        "escalation_id": escalation_id,
        "servicenow_incident": servicenow_incident,
        "specialist_chat_url": specialist_url,  # NEW: Direct link for specialist to join
        "status": status,
        "assigned_to": assigned["name"] if assigned else "Next Available",
        "assigned_email": assigned["email"] if assigned else f"{department.lower()}@company.com",
        "department": department,
        "urgency": urgency,
        "expected_response": response_time,
        "message": message,
        "notifications_sent": notification_results,
        "next_steps": [
            f"Escalation ID: {escalation_id} - save this for reference",
            f"ServiceNow Ticket: {servicenow_incident}" if servicenow_incident else "ServiceNow ticket pending",
            "The specialist has been notified via Teams and Email with a direct chat link",
            f"Expected response time: {response_time}"
        ]
    }


def find_expert(
    topic: str,
    department: str
) -> dict:
    """
    Find the best expert for a specific topic.
    
    Args:
        topic: The topic or issue requiring expertise
        department: Department filter (IT_Support, HR, Sales, Legal) - use empty string for all
    
    Returns:
        dict: List of relevant experts with availability
    """
    topic_lower = topic.lower()
    matches = []
    
    departments_to_search = [department] if department else SPECIALISTS.keys()
    
    for dept in departments_to_search:
        if dept not in SPECIALISTS:
            continue
        for specialist in SPECIALISTS[dept]:
            # Check if topic matches any expertise
            relevance = sum(1 for exp in specialist["expertise"] if exp in topic_lower or topic_lower in exp)
            if relevance > 0 or not topic:  # Include all if no specific topic
                matches.append({
                    "name": specialist["name"],
                    "email": specialist["email"],
                    "department": dept,
                    "expertise": specialist["expertise"],
                    "available": specialist["available"],
                    "relevance_score": relevance
                })
    
    # Sort by relevance and availability
    matches.sort(key=lambda x: (x["available"], x["relevance_score"]), reverse=True)
    
    return {
        "topic": topic,
        "experts_found": len(matches),
        "experts": matches[:5],
        "recommendation": matches[0]["name"] if matches and matches[0]["available"] else "No available experts found"
    }


def schedule_callback(
    department: str,
    preferred_time: str,
    phone_number: str,
    issue_summary: str,
    employee_id: str
) -> dict:
    """
    Schedule a callback from a specialist.
    
    Args:
        department: Department to callback from
        preferred_time: Preferred callback time (e.g., "today 2pm", "tomorrow morning")
        phone_number: Phone number to call
        issue_summary: Brief description of the issue
        employee_id: The employee's ID (use 'unknown' if not known)
    
    Returns:
        dict: Callback confirmation details
    """
    callback_id = f"CB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Parse preferred time (simplified)
    now = datetime.now()
    if "today" in preferred_time.lower():
        scheduled = now.replace(hour=14, minute=0)  # Default to 2 PM
    elif "tomorrow" in preferred_time.lower():
        scheduled = (now + timedelta(days=1)).replace(hour=10, minute=0)
    else:
        scheduled = now + timedelta(hours=4)  # Default to 4 hours from now
    
    return {
        "callback_id": callback_id,
        "status": "scheduled",
        "department": department,
        "scheduled_time": scheduled.strftime("%Y-%m-%d %H:%M"),
        "phone_number": phone_number,
        "employee_id": employee_id,
        "issue_summary": issue_summary,
        "confirmation": f"A {department} specialist will call you at {scheduled.strftime('%I:%M %p on %B %d')}",
        "notes": [
            "Please ensure your phone is available at the scheduled time",
            "If you miss the call, we'll try again within 30 minutes",
            "You can reschedule by replying to the confirmation email"
        ]
    }


def start_live_chat(
    department: str,
    initial_message: str,
    employee_id: str
) -> dict:
    """
    Initiate a live chat session with a human agent.
    
    Args:
        department: Department for live chat
        initial_message: The user's initial message/issue
        employee_id: The employee's ID (use 'unknown' if not known)
    
    Returns:
        dict: Live chat session details
    """
    escalation_id = f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    specialist_token = secrets.token_urlsafe(32)
    
    # Check for available agents
    specialists = SPECIALISTS.get(department, [])
    available = [s for s in specialists if s["available"]]
    
    # ============================================================
    # CREATE SERVICENOW INCIDENT
    # ============================================================
    servicenow_incident = None
    servicenow_result = create_servicenow_incident(
        escalation_id=escalation_id,
        department=department,
        employee_id=employee_id,
        issue_summary=initial_message,
        urgency="normal",
        assigned_to=available[0]["name"] if available else None,
        caller_email=employee_id
    )
    if servicenow_result.get("created"):
        servicenow_incident = servicenow_result.get("incident_number")
        print(f"ServiceNow incident created: {servicenow_incident}")
    else:
        print(f"ServiceNow ticket not created: {servicenow_result.get('reason', 'Unknown error')}")
    
    # Register session with the server (non-blocking)
    session_data = {
        "escalation_id": escalation_id,
        "specialist_token": specialist_token,
        "department": department,
        "urgency": "normal",
        "issue_summary": initial_message,
        "employee_id": employee_id,
        "servicenow_incident": servicenow_incident,
    }
    
    def register_session():
        """Background registration."""
        import time
        time.sleep(0.5)
        try:
            if REQUESTS_AVAILABLE:
                response = requests.post(
                    f"{APP_BASE_URL}/api/escalation/register",
                    json=session_data,
                    timeout=10
                )
                if response.status_code == 200:
                    print(f"Live chat session registered: {escalation_id}")
        except Exception as e:
            print(f"Session registration error: {e}")
    
    import threading
    thread = threading.Thread(target=register_session, daemon=True)
    thread.start()
    
    # Generate specialist URL
    specialist_url = f"{APP_BASE_URL}/specialist?escalation_id={escalation_id}&token={specialist_token}"
    
    if available:
        assigned = available[0]
        
        # Send notification to specialist
        _notify_specialist(
            specialist=assigned,
            department=department,
            escalation_id=escalation_id,
            employee_id=employee_id,
            issue_summary=initial_message,
            urgency="normal",
            specialist_url=specialist_url
        )
        
        return {
            "escalation_id": escalation_id,
            "session_id": escalation_id,
            "servicenow_incident": servicenow_incident,
            "status": "connected",
            "chat_url": specialist_url,
            "agent_name": assigned["name"],
            "department": department,
            "message": f"Live chat session {escalation_id} started. You're now connected with {assigned['name']} from {department}. They can see your conversation history and will respond shortly.",
            "estimated_wait": "0 minutes"
        }
    else:
        # Queue position simulation
        queue_position = 3
        return {
            "escalation_id": escalation_id,
            "session_id": escalation_id,
            "servicenow_incident": servicenow_incident,
            "status": "queued",
            "chat_url": specialist_url,
            "queue_position": queue_position,
            "department": department,
            "message": f"Session {escalation_id} created. All agents are currently busy. You're #{queue_position} in queue.",
            "estimated_wait": f"{queue_position * 5} minutes"
        }


def check_specialist_availability(department: str) -> dict:
    """
    Check current availability of specialists in a department.
    
    Args:
        department: The department to check (IT_Support, HR, Sales, Legal)
    
    Returns:
        dict: Availability status for the department
    """
    if department not in SPECIALISTS:
        return {
            "department": department,
            "error": f"Unknown department: {department}",
            "valid_departments": list(SPECIALISTS.keys())
        }
    
    specialists = SPECIALISTS[department]
    available = [s for s in specialists if s["available"]]
    
    return {
        "department": department,
        "total_specialists": len(specialists),
        "available_count": len(available),
        "available_specialists": [
            {"name": s["name"], "expertise": s["expertise"]} 
            for s in available
        ],
        "busy_specialists": [
            s["name"] for s in specialists if not s["available"]
        ],
        "recommendation": "Live chat available" if available else "Schedule a callback instead"
    }
