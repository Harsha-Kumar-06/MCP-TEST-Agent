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
    res = svc.get_user_by_email(email)
    logger.info(f"jira_get_user_by_email({email}) -> {res}")
    return res


def jira_invite_user(email: str) -> dict[str, Any]:
    """
    Invite a new user to Jira by email address.
    Use this when a user doesn't exist in Jira yet and needs to be invited.
    The user will receive an email invitation to create their Jira account.
    
    email: The email address to send the invitation to.
    """
    logger.info(f"jira_invite_user(email={email})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no invitation sent."}
    
    # First check if user already exists
    existing_user = svc.get_user_by_email(email)
    if existing_user.get("status") == "success":
        return {
            "status": "error",
            "error": f"User with email {email} already exists in Jira (Display Name: {existing_user.get('display_name')}). Use jira_grant_access to add them to a project.",
            "already_exists": True,
            "account_id": existing_user.get("account_id"),
            "display_name": existing_user.get("display_name")
        }
    
    res = svc.invite_user(email)
    logger.info(f"jira_invite_user result: {res}")
    return res


def jira_invite_and_grant_access(
    user_email: str, project_key: str, role_name: str
) -> dict[str, Any]:
    """
    Invite a user to Jira AND grant them access to a project in one step.
    Use this when you want to invite a new user and immediately give them project access.
    If the user already exists, it will just grant them the project role.
    
    user_email: The email address of the user to invite.
    project_key: Jira project key (e.g. KAN).
    role_name: e.g. Administrator, Member, Viewer. REQUIRED.
    """
    logger.info(f"jira_invite_and_grant_access(user_email={user_email}, project_key={project_key}, role_name={role_name})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    
    # 1. Check if user exists, if not invite them
    user = svc.get_user_by_email(user_email)
    invited = False
    
    if user.get("status") != "success":
        # User doesn't exist, try to invite them
        logger.info(f"User {user_email} not found, sending invitation...")
        invite_result = svc.invite_user(user_email)
        
        if invite_result.get("status") != "success":
            return {
                "status": "error",
                "error": f"Could not invite user {user_email}. Error: {invite_result.get('error')}",
                "invite_error": invite_result.get("error")
            }
        
        invited = True
        # Re-fetch the user after invitation
        import time
        time.sleep(1)  # Give Jira a moment to process the invitation
        user = svc.get_user_by_email(user_email)
        
        if user.get("status") != "success":
            # User was invited but not yet in the system - this is expected
            return {
                "status": "success",
                "message": f"Invitation sent to {user_email}. Once they accept the invitation and create their account, you can grant them access to the project.",
                "invited": True,
                "pending_access": True,
                "project_key": project_key,
                "role_name": role_name
            }
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    # 2. Resolve Project Key
    projects_resp, _ = svc._request("GET", "project")
    real_project_key = project_key.upper()
    project_name = project_key
    if projects_resp and isinstance(projects_resp, list):
        for p in projects_resp:
            if p.get("name", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                project_name = p.get("name")
                break
            if p.get("key", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                project_name = p.get("name", real_project_key)
                break
    
    # 3. Get Project Roles
    roles_resp = svc.get_project_roles(real_project_key)
    if roles_resp.get("status") != "success":
        base_msg = f"Invitation sent to {user_email}. " if invited else ""
        return {
            "status": "partial" if invited else "error",
            "error": f"{base_msg}However, could not fetch roles for project {real_project_key}. Error: {roles_resp.get('error')}",
            "invited": invited
        }
    
    roles = roles_resp.get("roles") or {}
    
    # 4. Match Role
    role_id = None
    matched_role_name = None
    for rid, rname in roles.items():
        if rname == role_name or (rname or "").lower() == (role_name or "").lower():
            role_id = rid
            matched_role_name = rname
            break
    
    if not role_id:
        base_msg = f"Invitation sent to {user_email}. " if invited else ""
        return {
            "status": "partial" if invited else "error",
            "error": f"{base_msg}However, role '{role_name}' not found. Available roles: {list(roles.values())}",
            "invited": invited,
            "available_roles": list(roles.values())
        }
    
    # 5. Check if user already has this role
    if svc.is_user_in_role(real_project_key, role_id, account_id):
        return {
            "status": "success",
            "message": f"User '{display_name}' already has the '{matched_role_name}' role in project '{project_name}'.",
            "invited": invited,
            "already_assigned": True
        }
    
    # 6. Grant the role
    res = svc.grant_project_role(real_project_key, account_id, role_id)
    
    if res.get("status") == "success":
        if svc.is_user_in_role(real_project_key, role_id, account_id):
            res["verified"] = True
            invite_msg = "Invited and added" if invited else "Added"
            res["message"] = f"{invite_msg} '{display_name}' to the '{matched_role_name}' role in project '{project_name}' ({real_project_key})."
        else:
            res["verified"] = False
            res["warning"] = "Grant API returned success but user not found in role."
        res["invited"] = invited
    
    logger.info(f"jira_invite_and_grant_access result: {res}")
    return res


def jira_grant_access(
    user_email: str, project_key: str, role_name: str
) -> dict[str, Any]:
    """
    Grant a user access to a Jira project by adding them to a project role.
    The user must already exist in Jira. If they don't exist, use jira_invite_and_grant_access instead.
    
    user_email: User's email.
    project_key: Jira project key (e.g. KAN). If a name is provided (e.g. "Space 1"), it tries to resolve it.
    role_name: e.g. Administrator, Member, Viewer. REQUIRED.
    """
    logger.info(f"jira_grant_access(user_email={user_email}, project_key={project_key}, role_name={role_name})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    
    # 1. Resolve User
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        logger.warning(f"jira_grant_access user lookup failed: {user}")
        return {
            "status": "error",
            "error": f"User '{user_email}' not found in Jira. Use jira_invite_and_grant_access to invite them first.",
            "user_not_found": True
        }
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    # 2. Resolve Project Key (if name provided)
    projects_resp, _ = svc._request("GET", "project")
    real_project_key = project_key.upper() 
    project_name = project_key
    if projects_resp and isinstance(projects_resp, list):
        for p in projects_resp:
            if p.get("name", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                project_name = p.get("name")
                break
            if p.get("key", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                project_name = p.get("name", real_project_key)
                break
    
    logger.info(f"Resolved project: {project_key} -> {real_project_key} ({project_name})")
    
    # 3. Get Project Roles
    roles_resp = svc.get_project_roles(real_project_key)
    if roles_resp.get("status") != "success":
        err_res = {"status": "error", "error": f"Could not fetch roles for project {real_project_key}. Check if project exists. Error: {roles_resp.get('error')}"}
        logger.warning(f"jira_grant_access failed: {err_res}")
        return err_res
        
    roles = roles_resp.get("roles") or {}
    
    # 4. Match Role
    role_id = None
    matched_role_name = None
    # Exact match
    for rid, rname in roles.items():
        if rname == role_name:
            role_id = rid
            matched_role_name = rname
            break
    # Case-insensitive match
    if not role_id:
        for rid, rname in roles.items():
            if (rname or "").lower() == (role_name or "").lower():
                role_id = rid
                matched_role_name = rname
                break
                
    if not role_id:
        err_res = {
            "status": "error",
            "error": f"Role '{role_name}' not found in project '{real_project_key}'. Available roles: {list(roles.values())}. Please select one of these exact roles.",
            "available_roles": list(roles.values())
        }
        logger.warning(f"jira_grant_access failed: {err_res}")
        return err_res
    
    # 5. Check if user already has this role
    if svc.is_user_in_role(real_project_key, role_id, account_id):
        res = {
            "status": "success",
            "message": f"User '{display_name}' already has the '{matched_role_name}' role in project '{project_name}' ({real_project_key}). No action needed.",
            "already_assigned": True
        }
        logger.info(f"jira_grant_access: {res}")
        return res
    
    # 6. Grant the role
    res = svc.grant_project_role(real_project_key, account_id, role_id)
    
    # 7. Verify the grant worked
    if res.get("status") == "success":
        if svc.is_user_in_role(real_project_key, role_id, account_id):
            res["verified"] = True
            res["message"] = f"Successfully added '{display_name}' to the '{matched_role_name}' role in project '{project_name}' ({real_project_key})."
        else:
            res["verified"] = False
            res["warning"] = "Grant API returned success but user not found in role. This may be a permission or Jira configuration issue."
    
    logger.info(f"jira_grant_access result: {res}")
    return res


def jira_revoke_access(
    user_email: str, project_key: str, role_name: str
) -> dict[str, Any]:
    """
    Revoke a user's access from a Jira project by removing them from a project role.
    user_email: User's email.
    project_key: Jira project key.
    role_name: e.g. Developers. REQUIRED.
    """
    logger.info(f"jira_revoke_access(user_email={user_email}, project_key={project_key}, role_name={role_name})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    
    # 1. Resolve User
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        logger.warning(f"jira_revoke_access user lookup failed: {user}")
        return user
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)

    # 2. Resolve Project Key
    projects_resp, _ = svc._request("GET", "project")
    real_project_key = project_key.upper()
    project_name = project_key
    if projects_resp and isinstance(projects_resp, list):
        for p in projects_resp:
            if p.get("name", "").lower() == project_key.lower() or p.get("key", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                project_name = p.get("name", real_project_key)
                break

    # 3. Get Roles to find ID
    roles_resp = svc.get_project_roles(real_project_key)
    if roles_resp.get("status") != "success":
        logger.warning(f"jira_revoke_access roles lookup failed: {roles_resp}")
        return roles_resp
    roles = roles_resp.get("roles") or {}
    
    role_id = None
    matched_role_name = None
    for rid, rname in roles.items():
        if (rname or "").lower() == (role_name or "").lower():
            role_id = rid
            matched_role_name = rname
            break
    if not role_id:
        err_res = {
            "status": "error",
            "error": f"Role '{role_name}' not found. Available: {list(roles.values())}. Cannot revoke.",
        }
        logger.warning(f"jira_revoke_access failed: {err_res}")
        return err_res
    
    # 4. Check if user actually has this role
    if not svc.is_user_in_role(real_project_key, role_id, account_id):
        res = {
            "status": "success",
            "message": f"User '{display_name}' does not have the '{matched_role_name}' role in project '{project_name}' ({real_project_key}). No action needed.",
            "already_removed": True
        }
        logger.info(f"jira_revoke_access: {res}")
        return res
    
    # 5. Revoke the role
    res = svc.revoke_project_role(real_project_key, account_id, role_id)
    
    # 6. Verify the revoke worked
    if res.get("status") == "success":
        if not svc.is_user_in_role(real_project_key, role_id, account_id):
            res["verified"] = True
            res["message"] = f"Successfully removed '{display_name}' from the '{matched_role_name}' role in project '{project_name}' ({real_project_key})."
        else:
            res["verified"] = False
            res["warning"] = "Revoke API returned success but user still found in role. This may be a permission or Jira configuration issue."
    
    logger.info(f"jira_revoke_access result: {res}")
    return res


def jira_list_user_access(user_email: str) -> dict[str, Any]:
    """
    List Jira projects (and optionally roles) for a user. Returns projects the user can access.
    """
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured.", "projects": []}
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        logger.warning(f"jira_list_user_access user lookup failed: {user}")
        return user
    account_id = user.get("account_id")
    if not account_id:
        return {"status": "error", "error": "No account_id for user"}
    
    res = svc.get_user_accessible_projects(account_id)
    logger.info(f"jira_list_user_access({user_email}) -> found {len(res.get('projects', []))} projects")
    logger.debug(f"Full access list: {res}")
    return res


def jira_list_project_roles(project_key: str) -> dict[str, Any]:
    """List available project roles for a Jira project (e.g. Developers, Administrators)."""
    res = get_jira_service().get_project_roles(project_key)
    logger.info(f"jira_list_project_roles({project_key}) -> {res}")
    return res


def jira_get_user_roles_in_project(user_email: str, project_key: str) -> dict[str, Any]:
    """
    Check what roles a user has in a specific Jira project.
    Useful for verifying current access before grant/revoke.
    """
    logger.info(f"jira_get_user_roles_in_project(user_email={user_email}, project_key={project_key})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured."}
    
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    # Resolve project key
    projects_resp, _ = svc._request("GET", "project")
    real_project_key = project_key.upper()
    project_name = project_key
    if projects_resp and isinstance(projects_resp, list):
        for p in projects_resp:
            if p.get("name", "").lower() == project_key.lower() or p.get("key", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                project_name = p.get("name", real_project_key)
                break
    
    res = svc.get_user_roles_in_project(real_project_key, account_id)
    if res.get("status") == "success":
        res["user_email"] = user_email
        res["display_name"] = display_name
        res["project_name"] = project_name
        role_names = [r["role_name"] for r in res.get("roles", [])]
        if role_names:
            res["message"] = f"'{display_name}' has the following roles in '{project_name}': {', '.join(role_names)}"
        else:
            res["message"] = f"'{display_name}' has no roles in '{project_name}'."
    
    logger.info(f"jira_get_user_roles_in_project result: {res}")
    return res


# ---------- Email tool (used by Email agent) ----------

from .email_service import get_email_service


def email_fetch_unread(limit: int = 10) -> dict[str, Any]:
    """
    Fetch unread emails from the inbox.
    Returns a list of emails with sender, subject, body, and metadata.
    Use this to check for new access requests or messages.
    
    limit: Maximum number of emails to fetch (default 10).
    """
    logger.info(f"email_fetch_unread(limit={limit})")
    svc = get_email_service()
    res = svc.fetch_unread_emails(limit=limit)
    logger.info(f"email_fetch_unread result: {res.get('count', 0)} emails found")
    return res


def email_get_by_id(email_id: str) -> dict[str, Any]:
    """
    Fetch a specific email by its ID.
    Use this to get full details of an email for processing.
    
    email_id: The ID of the email to fetch.
    """
    logger.info(f"email_get_by_id(email_id={email_id})")
    svc = get_email_service()
    res = svc.fetch_email_by_id(email_id)
    logger.info(f"email_get_by_id result: {res.get('status')}")
    return res


def email_mark_as_read(email_id: str) -> dict[str, Any]:
    """
    Mark an email as read.
    Use this after processing an email to prevent re-processing.
    
    email_id: The ID of the email to mark as read.
    """
    logger.info(f"email_mark_as_read(email_id={email_id})")
    svc = get_email_service()
    res = svc.mark_as_read(email_id)
    logger.info(f"email_mark_as_read result: {res}")
    return res


def email_search(query: str, limit: int = 10) -> dict[str, Any]:
    """
    Search emails using IMAP search criteria.
    
    query: IMAP search query. Examples:
        - 'FROM "user@example.com"' - emails from specific sender
        - 'SUBJECT "access request"' - emails with subject containing text
        - 'SINCE 01-Jan-2026' - emails since a date
        - 'UNSEEN' - unread emails
        - 'FROM "user@example.com" SUBJECT "jira"' - combined criteria
    limit: Maximum results (default 10).
    """
    logger.info(f"email_search(query={query}, limit={limit})")
    svc = get_email_service()
    res = svc.search_emails(query=query, limit=limit)
    logger.info(f"email_search result: {res.get('count', 0)} emails found")
    return res


def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """
    Send an email. 
    to: recipient address. 
    subject: subject line. 
    body: plain text body.
    """
    logger.info(f"send_email(to={to}, subject={subject})")
    svc = get_email_service()
    res = svc.send_email(to=to, subject=subject, body=body)
    logger.info(f"send_email result: {res}")
    return res


def email_reply(
    original_email_id: str,
    reply_body: str,
    include_original: bool = True
) -> dict[str, Any]:
    """
    Reply to an email, maintaining the thread/conversation.
    
    original_email_id: The ID of the email to reply to.
    reply_body: The reply message body.
    include_original: Whether to include the original message (default True).
    """
    logger.info(f"email_reply(original_email_id={original_email_id})")
    svc = get_email_service()
    
    # First fetch the original email
    original = svc.fetch_email_by_id(original_email_id)
    if original.get("status") != "success":
        return {"status": "error", "error": f"Could not fetch original email: {original.get('error')}"}
    
    res = svc.send_reply(
        original_email=original["email"],
        body=reply_body,
        include_original=include_original
    )
    logger.info(f"email_reply result: {res}")
    return res


def email_send_followup(
    to: str,
    original_subject: str,
    body: str,
    context: str = ""
) -> dict[str, Any]:
    """
    Send a follow-up email asking for more information.
    
    to: Recipient email address.
    original_subject: The subject of the original conversation.
    body: The follow-up question/message.
    context: Optional context about what information is needed and why.
    """
    logger.info(f"email_send_followup(to={to}, subject={original_subject})")
    svc = get_email_service()
    
    # Add Re: if not present
    if not original_subject.lower().startswith("re:"):
        subject = f"Re: {original_subject}"
    else:
        subject = original_subject
    
    # Build a professional follow-up message
    full_body = f"""Hi,

{body}

{f"Context: {context}" if context else ""}

Please reply to this email with the requested information.

Best regards,
Access Controller Bot"""
    
    res = svc.send_email(to=to, subject=subject, body=full_body.strip())
    logger.info(f"email_send_followup result: {res}")
    return res

