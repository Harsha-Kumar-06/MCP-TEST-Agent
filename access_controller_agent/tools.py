"""
Tools for the Access Controller agent: Jira (grant/revoke/list, user lookup) and Email (send).
"""
from __future__ import annotations

import os
import logging
from typing import Any

from .jira_service import get_jira_service

logger = logging.getLogger(__name__)


# ---------- Jira tools (used by Jira agent) ----------

def jira_get_user_by_email(email: str) -> dict[str, Any]:
    """Look up a Jira user by email. Returns account_id, display_name, or error."""
    svc = get_jira_service()
    return svc.get_user_by_email(email)


def jira_grant_access(
    user_email: str, project_key: str, role_name: str = "Developers"
) -> dict[str, Any]:
    """
    Grant a user access to a Jira project by adding them to a project role.
    user_email: User's email. project_key: Jira project key (e.g. PROJ). role_name: e.g. Developers, Administrators, Users.
    """
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    account_id = user.get("account_id")
    if not account_id:
        return {"status": "error", "error": "No account_id for user"}
    roles_resp = svc.get_project_roles(project_key)
    if roles_resp.get("status") != "success":
        return roles_resp
    roles = roles_resp.get("roles") or {}
    role_id = None
    for rid, rname in roles.items():
        if (rname or "").lower() == (role_name or "").lower():
            role_id = rid
            break
    if not role_id:
        return {
            "status": "error",
            "error": f"Role '{role_name}' not found. Available: {list(roles.values())}",
        }
    return svc.grant_project_role(project_key, account_id, role_id)


def jira_revoke_access(
    user_email: str, project_key: str, role_name: str = "Developers"
) -> dict[str, Any]:
    """
    Revoke a user's access from a Jira project by removing them from a project role.
    user_email: User's email. project_key: Jira project key. role_name: e.g. Developers.
    """
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    account_id = user.get("account_id")
    if not account_id:
        return {"status": "error", "error": "No account_id for user"}
    roles_resp = svc.get_project_roles(project_key)
    if roles_resp.get("status") != "success":
        return roles_resp
    roles = roles_resp.get("roles") or {}
    role_id = None
    for rid, rname in roles.items():
        if (rname or "").lower() == (role_name or "").lower():
            role_id = rid
            break
    if not role_id:
        return {
            "status": "error",
            "error": f"Role '{role_name}' not found. Available: {list(roles.values())}",
        }
    return svc.revoke_project_role(project_key, account_id, role_id)


def jira_list_user_access(user_email: str) -> dict[str, Any]:
    """
    List Jira projects (and optionally roles) for a user. Returns projects the user can access.
    """
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured.", "projects": []}
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    account_id = user.get("account_id")
    if not account_id:
        return {"status": "error", "error": "No account_id for user"}
    return svc.get_user_accessible_projects(account_id)


def jira_list_project_roles(project_key: str) -> dict[str, Any]:
    """List available project roles for a Jira project (e.g. Developers, Administrators)."""
    return get_jira_service().get_project_roles(project_key)


# ---------- Email tool (used by Email agent) ----------

def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """
    Send an email. to: recipient address. subject: subject line. body: plain text body.
    When SMTP is not configured, logs the email and returns success (for testing).
    """
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "0") or "0")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_addr = os.getenv("EMAIL_FROM", "access-bot@company.com")
    if smtp_host and smtp_port and smtp_user and smtp_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = from_addr
            msg["To"] = to
            msg.attach(MIMEText(body, "plain"))
            with smtplib.SMTP(smtp_host, smtp_port) as s:
                s.starttls()
                s.login(smtp_user, smtp_password)
                s.sendmail(from_addr, [to], msg.as_string())
            logger.info("Email sent to %s", to)
            return {"status": "success", "message": f"Email sent to {to}"}
        except Exception as e:
            logger.exception("Send email failed: %s", e)
            return {"status": "error", "error": str(e)}
    logger.info("[Mock] Email would send to=%s subject=%s body_len=%s", to, subject, len(body))
    return {"status": "success", "message": f"Email queued (mock) to {to}"}
