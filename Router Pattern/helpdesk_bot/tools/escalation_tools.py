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

# For timezone handling
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo  # For older Python versions

import re


# Timezone abbreviation to IANA timezone mapping
TIMEZONE_ABBREVIATIONS = {
    # US timezones
    "est": "America/New_York",
    "eastern": "America/New_York",
    "edt": "America/New_York",
    "cst": "America/Chicago",
    "central": "America/Chicago",
    "cdt": "America/Chicago",
    "mst": "America/Denver",
    "mountain": "America/Denver",
    "mdt": "America/Denver",
    "pst": "America/Los_Angeles",
    "pacific": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "akst": "America/Anchorage",
    "alaska": "America/Anchorage",
    "hst": "Pacific/Honolulu",
    "hawaii": "Pacific/Honolulu",
    # International
    "gmt": "Europe/London",
    "utc": "UTC",
    "bst": "Europe/London",
    "cet": "Europe/Paris",
    "cest": "Europe/Paris",
    "ist": "Asia/Kolkata",
    "jst": "Asia/Tokyo",
    "aest": "Australia/Sydney",
    "aedt": "Australia/Sydney",
}


def normalize_timezone(timezone_str: str) -> str:
    """
    Normalize timezone string - convert abbreviations to IANA timezone names.
    
    Args:
        timezone_str: Timezone as abbreviation (e.g., "EST", "PST") or IANA name
    
    Returns:
        str: IANA timezone name (e.g., "America/New_York")
    """
    if not timezone_str:
        return None
    
    tz_lower = timezone_str.strip().lower()
    
    # Check if it's an abbreviation
    if tz_lower in TIMEZONE_ABBREVIATIONS:
        return TIMEZONE_ABBREVIATIONS[tz_lower]
    
    # Otherwise return as-is (assume it's already IANA format)
    return timezone_str.strip()


def get_current_time_info(user_timezone: str = None) -> dict:
    """
    Get current date/time information, optionally in a specific timezone.
    
    Args:
        user_timezone: User's timezone (e.g., "America/New_York", "EST", "Pacific")
    
    Returns:
        dict: Current time information with formatted strings
    """
    # Server time
    server_now = datetime.now()
    
    result = {
        "server_time": server_now.strftime("%Y-%m-%d %H:%M:%S"),
        "server_date": server_now.strftime("%B %d, %Y"),
        "server_day": server_now.strftime("%A"),
    }
    
    # User's local time if timezone provided
    if user_timezone:
        # Normalize timezone abbreviations to IANA names
        normalized_tz = normalize_timezone(user_timezone)
        try:
            user_tz = ZoneInfo(normalized_tz)
            user_now = datetime.now(user_tz)
            result["user_timezone"] = normalized_tz
            result["user_timezone_input"] = user_timezone  # Keep original input
            result["user_time"] = user_now.strftime("%I:%M %p")
            result["user_time_24h"] = user_now.strftime("%H:%M")
            result["user_date"] = user_now.strftime("%B %d, %Y")
            result["user_day"] = user_now.strftime("%A")
            result["user_datetime"] = user_now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Business hours check (8 AM - 6 PM)
            result["is_business_hours"] = 8 <= user_now.hour < 18
            result["is_weekend"] = user_now.weekday() >= 5
        except Exception as e:
            result["timezone_error"] = f"Invalid timezone: {user_timezone}"
    
    return result

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
    employee_id: str,
    user_timezone: str = None
) -> dict:
    """
    Schedule a callback from a specialist.
    
    Args:
        department: Department to callback from
        preferred_time: Preferred callback time (e.g., "today 2pm", "tomorrow morning", "3/5/2026 10:00am")
        phone_number: Phone number to call
        issue_summary: Brief description of the issue
        employee_id: The employee's ID (use 'unknown' if not known)
        user_timezone: User's timezone (e.g., "America/New_York", "EST", "Pacific"). 
                       If not provided, will use server time.
    
    Returns:
        dict: Callback confirmation details
    """
    callback_id = f"CB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Normalize timezone abbreviations to IANA names
    normalized_tz = normalize_timezone(user_timezone) if user_timezone else None
    
    # Set up timezone handling
    user_tz = None
    try:
        if normalized_tz:
            user_tz = ZoneInfo(normalized_tz)
    except Exception as e:
        print(f"Invalid timezone '{user_timezone}' (normalized: '{normalized_tz}'), using server time: {e}")
        user_tz = None
    
    # Get current time in user's timezone
    if user_tz:
        now = datetime.now(user_tz)
    else:
        now = datetime.now()
    
    # Parse preferred time intelligently
    preferred_lower = preferred_time.lower().strip()
    scheduled = None
    
    # First, try to extract an explicit date (e.g., "3/5/2026", "2026-03-05", "March 5, 2026")
    explicit_date = None
    
    # Match MM/DD/YYYY or M/D/YYYY format
    date_match_mdy = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', preferred_time)
    # Match YYYY-MM-DD format
    date_match_ymd = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', preferred_time)
    # Match "March 5, 2026" or "Mar 5 2026" style
    date_match_text = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{1,2}),?\s*(\d{4})', preferred_lower)
    
    if date_match_mdy:
        month = int(date_match_mdy.group(1))
        day = int(date_match_mdy.group(2))
        year = int(date_match_mdy.group(3))
        try:
            explicit_date = datetime(year, month, day).date()
        except ValueError:
            pass  # Invalid date, will fall through to other parsing
    elif date_match_ymd:
        year = int(date_match_ymd.group(1))
        month = int(date_match_ymd.group(2))
        day = int(date_match_ymd.group(3))
        try:
            explicit_date = datetime(year, month, day).date()
        except ValueError:
            pass
    elif date_match_text:
        month_names = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                       'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
        month = month_names.get(date_match_text.group(1)[:3], 1)
        day = int(date_match_text.group(2))
        year = int(date_match_text.group(3))
        try:
            explicit_date = datetime(year, month, day).date()
        except ValueError:
            pass
    
    # Extract time patterns - look for time after any date pattern or standalone
    # Supports: "10:00", "14:00", "10:00am", "2pm", "14" (24-hour standalone)
    # Pattern 1: HH:MM with optional am/pm (e.g., "10:00", "14:30", "10:00am")
    # Pattern 2: H/HH followed by am/pm (e.g., "2pm", "10am")  
    # Pattern 3: Standalone 24-hour format (13-23 range, since 1-12 is ambiguous)
    time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?|(\d{1,2})\s*(am|pm)', preferred_lower, re.IGNORECASE)
    
    # Also check for standalone 24-hour time (13-23) without am/pm
    standalone_24h = re.search(r'\b(1[3-9]|2[0-3])\b(?![\d:/])', preferred_time)
    
    if time_match:
        if time_match.group(4):  # Format like "10am" or "2pm"
            hour = int(time_match.group(4))
            minute = 0
            am_pm = time_match.group(5)
        else:  # Format like "10:00", "14:00", or "10:00am"
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            am_pm = time_match.group(3)
        
        # Convert to 24-hour format (only if am/pm specified)
        if am_pm:
            if am_pm.lower() == 'pm' and hour != 12:
                hour += 12
            elif am_pm.lower() == 'am' and hour == 12:
                hour = 0
        
        # Validate hour is in valid range
        if hour > 23:
            hour = 23  # Cap at 23:xx
        
        # Determine the date
        if explicit_date:
            scheduled_date = explicit_date
        elif 'tomorrow' in preferred_lower:
            scheduled_date = now.date() + timedelta(days=1)
        elif 'today' in preferred_lower:
            scheduled_date = now.date()
            # If the time has already passed today, schedule for tomorrow
            if user_tz:
                check_time = datetime(now.year, now.month, now.day, hour, minute, tzinfo=user_tz)
            else:
                check_time = datetime(now.year, now.month, now.day, hour, minute)
            if check_time < now:
                scheduled_date = now.date() + timedelta(days=1)
        else:
            # No explicit date, assume today but bump to tomorrow if time passed
            scheduled_date = now.date()
            if user_tz:
                check_time = datetime(now.year, now.month, now.day, hour, minute, tzinfo=user_tz)
            else:
                check_time = datetime(now.year, now.month, now.day, hour, minute)
            if check_time < now:
                scheduled_date = now.date() + timedelta(days=1)
        
        if user_tz:
            scheduled = datetime(scheduled_date.year, scheduled_date.month, scheduled_date.day, 
                               hour, minute, tzinfo=user_tz)
        else:
            scheduled = datetime(scheduled_date.year, scheduled_date.month, scheduled_date.day, 
                               hour, minute)
    
    # Handle standalone 24-hour format without minutes (e.g., "3/5/2026 14")
    elif standalone_24h:
        hour = int(standalone_24h.group(1))
        minute = 0
        scheduled_date = explicit_date if explicit_date else now.date()
        
        if user_tz:
            scheduled = datetime(scheduled_date.year, scheduled_date.month, scheduled_date.day, 
                               hour, minute, tzinfo=user_tz)
        else:
            scheduled = datetime(scheduled_date.year, scheduled_date.month, scheduled_date.day, 
                               hour, minute)
    
    # Handle relative time expressions
    elif 'morning' in preferred_lower:
        target_hour = 10
        target_date = explicit_date if explicit_date else (now.date() + timedelta(days=1) if 'tomorrow' in preferred_lower else now.date())
        if user_tz:
            scheduled = datetime(target_date.year, target_date.month, target_date.day, 
                               target_hour, 0, tzinfo=user_tz)
        else:
            scheduled = datetime(target_date.year, target_date.month, target_date.day, target_hour, 0)
    
    elif 'afternoon' in preferred_lower:
        target_hour = 14
        target_date = explicit_date if explicit_date else (now.date() + timedelta(days=1) if 'tomorrow' in preferred_lower else now.date())
        if user_tz:
            scheduled = datetime(target_date.year, target_date.month, target_date.day, 
                               target_hour, 0, tzinfo=user_tz)
        else:
            scheduled = datetime(target_date.year, target_date.month, target_date.day, target_hour, 0)
    
    elif 'evening' in preferred_lower:
        target_hour = 17
        target_date = explicit_date if explicit_date else (now.date() + timedelta(days=1) if 'tomorrow' in preferred_lower else now.date())
        if user_tz:
            scheduled = datetime(target_date.year, target_date.month, target_date.day, 
                               target_hour, 0, tzinfo=user_tz)
        else:
            scheduled = datetime(target_date.year, target_date.month, target_date.day, target_hour, 0)
    
    # Default fallback
    if not scheduled:
        if explicit_date:
            # Explicit date given but no time - default to 10 AM on that date
            if user_tz:
                scheduled = datetime(explicit_date.year, explicit_date.month, explicit_date.day, 
                                   10, 0, tzinfo=user_tz)
            else:
                scheduled = datetime(explicit_date.year, explicit_date.month, explicit_date.day, 10, 0)
        elif 'today' in preferred_lower:
            if user_tz:
                scheduled = now.replace(hour=14, minute=0, second=0, microsecond=0)
            else:
                scheduled = now.replace(hour=14, minute=0, second=0, microsecond=0)
            # If 2 PM has passed, go to 4 hours from now
            if scheduled < now:
                scheduled = now + timedelta(hours=4)
        elif 'tomorrow' in preferred_lower:
            next_day = now + timedelta(days=1)
            if user_tz:
                scheduled = next_day.replace(hour=10, minute=0, second=0, microsecond=0)
            else:
                scheduled = next_day.replace(hour=10, minute=0, second=0, microsecond=0)
        else:
            # Default to 4 hours from now
            scheduled = now + timedelta(hours=4)
    
    # Ensure scheduled time is during business hours (8 AM - 6 PM in user's timezone)
    if scheduled.hour < 8:
        scheduled = scheduled.replace(hour=8, minute=0)
    elif scheduled.hour >= 18:
        # Move to next business day at 9 AM
        scheduled = (scheduled + timedelta(days=1)).replace(hour=9, minute=0)
    
    # Format the time nicely for the user
    time_format_str = scheduled.strftime('%I:%M %p on %B %d, %Y')
    display_tz = normalized_tz or "server time"
    timezone_info = f" ({display_tz})"
    
    return {
        "callback_id": callback_id,
        "status": "scheduled",
        "department": department,
        "scheduled_time": scheduled.strftime("%Y-%m-%d %H:%M"),
        "scheduled_time_display": time_format_str,
        "timezone": normalized_tz or "server",
        "timezone_input": user_timezone,  # Original input for reference
        "phone_number": phone_number,
        "employee_id": employee_id,
        "issue_summary": issue_summary,
        "confirmation": f"A {department} specialist will call you at {time_format_str}{timezone_info}",
        "notes": [
            "Please ensure your phone is available at the scheduled time",
            "If you miss the call, we'll try again within 30 minutes",
            "You can reschedule by replying to the confirmation email"
        ]
    }


def start_live_chat(
    department: str,
    initial_message: str,
    employee_id: str,
    servicenow_only: bool = False
) -> dict:
    """
    Initiate a live chat session with a human agent.
    
    Args:
        department: Department for live chat
        initial_message: The user's initial message/issue
        employee_id: The employee's ID (use 'unknown' if not known)
        servicenow_only: If True, only creates a ServiceNow ticket without live chat capability.
                        Use this when no specialists are configured for live chat.
    
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
    
    # If ServiceNow-only mode, return without live chat capability
    if servicenow_only or (SERVICENOW_CONFIG.get("enabled") and not available):
        return {
            "escalation_id": escalation_id,
            "session_id": escalation_id,
            "servicenow_incident": servicenow_incident,
            "status": "servicenow_only",
            "servicenow_only": True,
            "chat_url": None,
            "department": department,
            "message": f"ServiceNow ticket {servicenow_incident or 'pending'} has been created. A specialist will respond to your request through the ticketing system. Live chat is not available for this request - all responses will be handled via ServiceNow.",
            "estimated_wait": "Response via ServiceNow within 4-8 hours",
            "notes": [
                "Your ticket has been logged in ServiceNow",
                "You will receive email updates on your ticket status",
                "Live chat is not available - specialists will respond via ServiceNow"
            ]
        }
    
    # Register session with the server (non-blocking)
    session_data = {
        "escalation_id": escalation_id,
        "specialist_token": specialist_token,
        "department": department,
        "urgency": "normal",
        "issue_summary": initial_message,
        "employee_id": employee_id,
        "servicenow_incident": servicenow_incident,
        "servicenow_only": False,
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
            "servicenow_only": False,
            "status": "waiting_for_specialist",
            "chat_url": specialist_url,
            "agent_name": assigned["name"],
            "department": department,
            "message": f"Live chat session {escalation_id} started. Waiting for {assigned['name']} from {department} to connect. You will be notified when they join the chat.",
            "estimated_wait": "1-5 minutes",
            "notes": [
                "A specialist has been notified and will join shortly",
                "You can send messages while waiting",
                "You will see a notification when the specialist connects"
            ]
        }
    else:
        # Queue position simulation - no one available but live chat is possible
        queue_position = 3
        return {
            "escalation_id": escalation_id,
            "session_id": escalation_id,
            "servicenow_incident": servicenow_incident,
            "servicenow_only": False,
            "status": "queued",
            "chat_url": specialist_url,
            "queue_position": queue_position,
            "department": department,
            "message": f"Session {escalation_id} created. All agents are currently busy. You're #{queue_position} in queue. You will be notified when a specialist becomes available.",
            "estimated_wait": f"{queue_position * 5} minutes",
            "notes": [
                f"You are #{queue_position} in the queue",
                "You can send messages while waiting",
                "You will be notified when a specialist joins"
            ]
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
