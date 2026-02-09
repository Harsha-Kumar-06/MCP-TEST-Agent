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
    Revoke a user's DIRECT access from a Jira project by removing them from a project role.
    Note: This only removes direct role assignments. If the user has access through a GROUP,
    use jira_get_user_access_details to check, then use jira_remove_user_from_group.
    
    user_email: User's email.
    project_key: Jira project key.
    role_name: e.g. Member, Administrator, Viewer. REQUIRED.
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
    
    # 4. Check detailed access (direct vs group-based)
    access_details = svc.get_user_access_details_in_project(real_project_key, account_id)
    
    # 4a. Check if user has DIRECT assignment to this role
    has_direct_role = False
    for dr in access_details.get("direct_roles", []):
        if dr.get("role_id") == role_id:
            has_direct_role = True
            break
    
    if not has_direct_role:
        # Check if they have access through a group
        group_access = []
        for gr in access_details.get("group_roles", []):
            if gr.get("role_id") == role_id:
                group_access.append(gr.get("via_group"))
        
        if group_access:
            return {
                "status": "error",
                "error": f"User '{display_name}' has the '{matched_role_name}' role in project '{project_name}' through GROUP membership, not direct assignment.",
                "group_based_access": True,
                "groups": group_access,
                "suggestion": f"To revoke access, remove the user from these groups: {group_access}. Use jira_remove_user_from_group tool."
            }
        else:
            return {
                "status": "success",
                "message": f"User '{display_name}' does not have the '{matched_role_name}' role in project '{project_name}' ({real_project_key}). No action needed.",
                "already_removed": True
            }
    
    # 5. Revoke the direct role
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


def jira_revoke_all_project_access(user_email: str, project_key: str) -> dict[str, Any]:
    """
    Revoke ALL of a user's access from a specific Jira project.
    This removes the user from ALL roles they have in the project (direct assignments only).
    
    Note: If user has access through groups, this will list those groups but cannot remove them
    automatically. Use jira_remove_user_from_group for group-based access.
    
    user_email: User's email.
    project_key: Jira project key.
    """
    logger.info(f"jira_revoke_all_project_access(user_email={user_email}, project_key={project_key})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    
    # 1. Resolve User
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
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
    
    # 3. Get detailed access info
    access_details = svc.get_user_access_details_in_project(real_project_key, account_id)
    if access_details.get("status") != "success":
        return access_details
    
    direct_roles = access_details.get("direct_roles", [])
    group_roles = access_details.get("group_roles", [])
    
    if not direct_roles and not group_roles:
        return {
            "status": "success",
            "message": f"User '{display_name}' has no access to project '{project_name}' ({real_project_key}). No action needed.",
            "already_removed": True
        }
    
    # 4. Remove all direct role assignments
    removed_roles = []
    failed_roles = []
    
    for role in direct_roles:
        role_id = role["role_id"]
        role_name = role["role_name"]
        res = svc.revoke_project_role(real_project_key, account_id, role_id)
        if res.get("status") == "success":
            removed_roles.append(role_name)
        else:
            failed_roles.append({"role": role_name, "error": res.get("error")})
    
    # 5. Build response
    result = {
        "status": "success" if not failed_roles else "partial",
        "user": display_name,
        "project": f"{project_name} ({real_project_key})",
        "removed_direct_roles": removed_roles,
    }
    
    if failed_roles:
        result["failed_roles"] = failed_roles
    
    if group_roles:
        groups = list(set(gr["via_group"] for gr in group_roles))
        result["warning"] = f"User also has access through group membership. Remove from these groups to fully revoke access: {groups}"
        result["access_granting_groups"] = groups
    
    if removed_roles:
        result["message"] = f"Removed '{display_name}' from {len(removed_roles)} role(s): {removed_roles}."
    elif group_roles:
        result["message"] = f"User has no direct roles but has access through groups: {access_details.get('access_granting_groups')}."
    else:
        result["message"] = f"No roles to remove."
    
    logger.info(f"jira_revoke_all_project_access result: {result}")
    return result


def jira_get_user_access_details(user_email: str, project_key: str) -> dict[str, Any]:
    """
    Get DETAILED access information for a user in a specific project.
    Shows both direct role assignments AND access through group membership.
    
    Use this to understand exactly HOW a user has access to a project before revoking.
    
    user_email: User's email.
    project_key: Jira project key.
    """
    logger.info(f"jira_get_user_access_details(user_email={user_email}, project_key={project_key})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured."}
    
    # Resolve user
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
    
    # Get detailed access
    res = svc.get_user_access_details_in_project(real_project_key, account_id)
    
    if res.get("status") == "success":
        res["user_email"] = user_email
        res["display_name"] = display_name
        res["project_name"] = project_name
        
        # Build helpful message
        direct = res.get("direct_roles", [])
        group = res.get("group_roles", [])
        
        if direct and group:
            res["message"] = f"'{display_name}' has {len(direct)} direct role(s) and {len(group)} role(s) via groups in '{project_name}'."
        elif direct:
            res["message"] = f"'{display_name}' has {len(direct)} direct role(s) in '{project_name}': {[r['role_name'] for r in direct]}."
        elif group:
            groups = res.get("access_granting_groups", [])
            res["message"] = f"'{display_name}' has access to '{project_name}' ONLY through group membership: {groups}."
        else:
            res["message"] = f"'{display_name}' has NO access to '{project_name}'."
    
    logger.info(f"jira_get_user_access_details result: {res}")
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


# ---------- Jira Group Management Tools ----------

def jira_list_groups(max_results: int = 50) -> dict[str, Any]:
    """
    List all groups in Jira.
    Groups are used to manage access at scale - instead of adding users to individual projects,
    you can add them to a group and the group to projects.
    
    max_results: Maximum number of groups to return (default 50).
    
    Returns a list of groups with their names.
    """
    logger.info(f"jira_list_groups(max_results={max_results})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured."}
    
    res = svc.list_groups(max_results=max_results)
    logger.info(f"jira_list_groups result: {res.get('total', 0)} groups found")
    return res


def jira_get_group_members(group_name: str, max_results: int = 50) -> dict[str, Any]:
    """
    Get members of a specific Jira group.
    
    group_name: The name of the group (e.g., "jira-software-users", "developers").
    max_results: Maximum number of members to return (default 50).
    
    Returns list of users in the group with their account IDs and display names.
    """
    logger.info(f"jira_get_group_members(group_name={group_name}, max_results={max_results})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured."}
    
    res = svc.get_group_members(group_name=group_name, max_results=max_results)
    logger.info(f"jira_get_group_members result: {res}")
    return res


def jira_add_user_to_group(user_email: str, group_name: str) -> dict[str, Any]:
    """
    Add a user to a Jira group.
    
    This is the RECOMMENDED way to manage access at scale:
    - Groups can be assigned to multiple projects at once
    - Adding a user to a group automatically gives them access to all projects the group has access to
    - Easier to manage than individual project role assignments
    
    user_email: The email of the user to add.
    group_name: The name of the group (e.g., "developers", "jira-software-users").
    """
    logger.info(f"jira_add_user_to_group(user_email={user_email}, group_name={group_name})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    
    # 1. Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return {
            "status": "error",
            "error": f"User '{user_email}' not found in Jira. Invite them first using jira_invite_user.",
            "user_not_found": True
        }
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    # 2. Check if already in group
    if svc.is_user_in_group(account_id, group_name):
        return {
            "status": "success",
            "message": f"'{display_name}' is already a member of group '{group_name}'.",
            "already_member": True
        }
    
    # 3. Add to group
    res = svc.add_user_to_group(account_id, group_name)
    
    # 4. Verify
    if res.get("status") == "success":
        if svc.is_user_in_group(account_id, group_name):
            res["verified"] = True
            res["message"] = f"Successfully added '{display_name}' to group '{group_name}'."
        else:
            res["verified"] = False
            res["warning"] = "API returned success but user not found in group."
    
    logger.info(f"jira_add_user_to_group result: {res}")
    return res


def jira_remove_user_from_group(user_email: str, group_name: str) -> dict[str, Any]:
    """
    Remove a user from a Jira group.
    
    This will revoke any access the user had through this group membership.
    
    user_email: The email of the user to remove.
    group_name: The name of the group.
    """
    logger.info(f"jira_remove_user_from_group(user_email={user_email}, group_name={group_name})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    
    # 1. Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    # 2. Check if in group
    if not svc.is_user_in_group(account_id, group_name):
        return {
            "status": "success",
            "message": f"'{display_name}' is not a member of group '{group_name}'. No action needed.",
            "already_removed": True
        }
    
    # 3. Remove from group
    res = svc.remove_user_from_group(account_id, group_name)
    
    # 4. Verify
    if res.get("status") == "success":
        if not svc.is_user_in_group(account_id, group_name):
            res["verified"] = True
            res["message"] = f"Successfully removed '{display_name}' from group '{group_name}'."
        else:
            res["verified"] = False
            res["warning"] = "API returned success but user still in group."
    
    logger.info(f"jira_remove_user_from_group result: {res}")
    return res


def jira_get_user_groups(user_email: str) -> dict[str, Any]:
    """
    Get all groups a user belongs to.
    
    Useful to understand a user's current access through group memberships.
    
    user_email: The email of the user.
    """
    logger.info(f"jira_get_user_groups(user_email={user_email})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured."}
    
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    res = svc.get_user_groups(account_id)
    if res.get("status") == "success":
        res["user_email"] = user_email
        res["display_name"] = display_name
        group_names = [g["name"] for g in res.get("groups", [])]
        if group_names:
            res["message"] = f"'{display_name}' is a member of: {', '.join(group_names)}"
        else:
            res["message"] = f"'{display_name}' is not a member of any groups."
    
    logger.info(f"jira_get_user_groups result: {res}")
    return res


# ---------- Jira Project Tools ----------

def jira_list_projects(max_results: int = 50) -> dict[str, Any]:
    """
    List all Jira projects.
    
    Use this to help users find the correct project key when they're unsure.
    Returns a list of projects with their keys (e.g., "PROJ", "KAN") and names.
    
    max_results: Maximum number of projects to return (default 50).
    """
    logger.info(f"jira_list_projects(max_results={max_results})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured."}
    
    res = svc.list_projects(max_results=max_results)
    logger.info(f"jira_list_projects result: {res.get('total', 0)} projects found")
    return res


def jira_get_project(project_key: str) -> dict[str, Any]:
    """
    Get details of a specific Jira project.
    
    project_key: The project key (e.g., "PROJ", "KAN") or project name.
    
    Returns project details including key, name, description, and lead.
    """
    logger.info(f"jira_get_project(project_key={project_key})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured."}
    
    # Try to resolve project key from name
    projects_resp, _ = svc._request("GET", "project")
    real_project_key = project_key.upper()
    if projects_resp and isinstance(projects_resp, list):
        for p in projects_resp:
            if p.get("name", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                break
            if p.get("key", "").lower() == project_key.lower():
                real_project_key = p.get("key")
                break
    
    res = svc.get_project_by_key(real_project_key)
    logger.info(f"jira_get_project result: {res}")
    return res


# ---------- Jira User Management Tools ----------

def jira_deactivate_user(user_email: str) -> dict[str, Any]:
    """
    Deactivate (remove) a user from Jira entirely.
    
    WARNING: This removes ALL of the user's access to Jira.
    Use this only when a user should no longer have any Jira access.
    
    For removing access from specific projects only, use jira_revoke_access instead.
    For removing from groups, use jira_remove_user_from_group instead.
    
    user_email: The email of the user to deactivate.
    """
    logger.info(f"jira_deactivate_user(user_email={user_email})")
    svc = get_jira_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Jira not configured; no change made."}
    
    # 1. Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    # 2. Deactivate
    res = svc.deactivate_user(account_id)
    
    if res.get("status") == "success":
        res["message"] = f"User '{display_name}' ({user_email}) has been deactivated from Jira."
    
    logger.info(f"jira_deactivate_user result: {res}")
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


# ==========================================================================
# CONFLUENCE TOOLS
# ==========================================================================

from .confluence_service import get_confluence_service


# ---------- Confluence Space Tools ----------

def confluence_list_spaces(limit: int = 50) -> dict[str, Any]:
    """
    List all Confluence spaces.
    
    Returns a list of spaces with their keys and names.
    Use this to help users find the correct space key.
    
    limit: Maximum number of spaces to return (default 50).
    """
    logger.info(f"confluence_list_spaces(limit={limit})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    res = svc.list_spaces(limit=limit)
    logger.info(f"confluence_list_spaces result: {res.get('total', 0)} spaces found")
    return res


def confluence_get_space(space_key: str) -> dict[str, Any]:
    """
    Get details of a specific Confluence space.
    
    space_key: The space key (e.g., "DEV", "TEAM").
    """
    logger.info(f"confluence_get_space(space_key={space_key})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    res = svc.get_space(space_key)
    logger.info(f"confluence_get_space result: {res}")
    return res


def confluence_get_space_permissions(space_key: str) -> dict[str, Any]:
    """
    Get permissions for a Confluence space.
    
    Shows all users and groups that have access to the space and their permission levels.
    
    space_key: The space key (e.g., "DEV", "TEAM").
    """
    logger.info(f"confluence_get_space_permissions(space_key={space_key})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    res = svc.get_space_permissions(space_key)
    logger.info(f"confluence_get_space_permissions result: {res}")
    return res


def confluence_grant_space_access(
    user_email: str, space_key: str, permission: str = "read"
) -> dict[str, Any]:
    """
    Grant a user access to a Confluence space.
    
    user_email: The user's email address.
    space_key: The space key (e.g., "DEV", "TEAM").
    permission: Permission level - "read" (view), "write" (edit), or "admin" (full control).
    """
    logger.info(f"confluence_grant_space_access(user_email={user_email}, space_key={space_key}, permission={permission})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    # Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return {
            "status": "error",
            "error": f"User '{user_email}' not found. They may need to be invited to Atlassian first.",
            "user_not_found": True
        }
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    res = svc.add_space_permission(space_key, account_id, permission)
    
    if res.get("status") == "success":
        res["message"] = f"Granted {permission} access to '{display_name}' for space '{space_key}'."
        res["user"] = display_name
    
    logger.info(f"confluence_grant_space_access result: {res}")
    return res


def confluence_revoke_space_access(user_email: str, space_key: str) -> dict[str, Any]:
    """
    Revoke a user's access from a Confluence space.
    
    Removes all permissions the user has for the specified space.
    
    user_email: The user's email address.
    space_key: The space key (e.g., "DEV", "TEAM").
    """
    logger.info(f"confluence_revoke_space_access(user_email={user_email}, space_key={space_key})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    # Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    res = svc.remove_space_permission(space_key, account_id)
    
    if res.get("status") == "success":
        res["user"] = display_name
        if not res.get("already_removed"):
            res["message"] = f"Revoked access for '{display_name}' from space '{space_key}'."
    
    logger.info(f"confluence_revoke_space_access result: {res}")
    return res


def confluence_add_group_to_space(
    group_name: str, space_key: str, permission: str = "read"
) -> dict[str, Any]:
    """
    Grant a group access to a Confluence space.
    
    group_name: The group name.
    space_key: The space key (e.g., "DEV", "TEAM").
    permission: Permission level - "read", "write", or "admin".
    """
    logger.info(f"confluence_add_group_to_space(group_name={group_name}, space_key={space_key}, permission={permission})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    res = svc.add_group_to_space(space_key, group_name, permission)
    logger.info(f"confluence_add_group_to_space result: {res}")
    return res


def confluence_list_user_access(user_email: str) -> dict[str, Any]:
    """
    List all Confluence spaces a user has access to.
    
    user_email: The user's email address.
    """
    logger.info(f"confluence_list_user_access(user_email={user_email})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    # Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    res = svc.get_user_space_permissions(account_id)
    
    if res.get("status") == "success":
        res["user_email"] = user_email
        res["display_name"] = display_name
        spaces = res.get("spaces", [])
        if spaces:
            res["message"] = f"'{display_name}' has access to {len(spaces)} space(s)."
        else:
            res["message"] = f"'{display_name}' has no Confluence space access."
    
    logger.info(f"confluence_list_user_access result: {res}")
    return res


# ---------- Confluence Group Tools ----------

def confluence_list_groups(limit: int = 50) -> dict[str, Any]:
    """
    List all Confluence groups.
    Note: These are the same groups as Jira (Atlassian Cloud shared directory).
    
    limit: Maximum number of groups to return.
    """
    logger.info(f"confluence_list_groups(limit={limit})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    res = svc.list_groups(limit=limit)
    logger.info(f"confluence_list_groups result: {res}")
    return res


def confluence_get_group_members(group_name: str, limit: int = 50) -> dict[str, Any]:
    """
    Get members of a Confluence group.
    
    group_name: The name of the group.
    limit: Maximum number of members to return.
    """
    logger.info(f"confluence_get_group_members(group_name={group_name}, limit={limit})")
    svc = get_confluence_service()
    if not svc.base_url or not svc._session.auth:
        return {"status": "skipped", "message": "Confluence not configured."}
    
    res = svc.get_group_members(group_name, limit=limit)
    logger.info(f"confluence_get_group_members result: {res}")
    return res


# ==========================================================================
# BITBUCKET TOOLS
# ==========================================================================

from .bitbucket_service import get_bitbucket_service


# ---------- Bitbucket Workspace Tools ----------

def bitbucket_list_workspaces() -> dict[str, Any]:
    """
    List all Bitbucket workspaces the authenticated user has access to.
    
    Workspaces are the top-level containers in Bitbucket that hold repositories.
    """
    logger.info("bitbucket_list_workspaces()")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.list_workspaces()
    logger.info(f"bitbucket_list_workspaces result: {res.get('total', 0)} workspaces found")
    return res


def bitbucket_get_workspace_members(workspace: str = None) -> dict[str, Any]:
    """
    Get all members of a Bitbucket workspace.
    
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_get_workspace_members(workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.get_workspace_members(workspace)
    logger.info(f"bitbucket_get_workspace_members result: {res}")
    return res


def bitbucket_add_workspace_member(user_email: str, workspace: str = None) -> dict[str, Any]:
    """
    Add a user to a Bitbucket workspace.
    
    This function automatically invites users to the workspace if they don't have access.
    Requires Atlassian Admin API configuration (ATLASSIAN_ORG_ID and ATLASSIAN_API_KEY).
    
    user_email: The user's email address.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_add_workspace_member(user_email={user_email}, workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    # Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return {
            "status": "error",
            "error": f"User '{user_email}' not found. They may need to be invited to Atlassian first.",
            "user_not_found": True
        }
    
    # Use account_id for Bitbucket API
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    if not account_id:
        return {
            "status": "error",
            "error": f"Could not find account_id for '{user_email}'",
        }
    
    res = svc.add_workspace_member(account_id, workspace, user_email)
    
    if res.get("status") == "success":
        res["user"] = display_name
        if res.get("invited"):
            if res.get("requires_acceptance"):
                res["message"] = f"✉️ Sent invitation to '{display_name}' ({user_email}). They must check their email and accept the invitation to activate Bitbucket access."
            else:
                res["message"] = f"Invited '{display_name}' to the workspace. They will receive an email invitation."
        else:
            res["message"] = f"Added '{display_name}' to workspace."
    
    logger.info(f"bitbucket_add_workspace_member result: {res}")
    return res


def bitbucket_remove_workspace_member(user_email: str, workspace: str = None) -> dict[str, Any]:
    """
    Remove a user from a Bitbucket workspace.
    
    user_email: The user's email address.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_remove_workspace_member(user_email={user_email}, workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    # Resolve user - pass workspace to search in workspace members
    user = svc.get_user_by_email(user_email, workspace)
    if user.get("status") != "success":
        return user
    
    # Use account_id for Bitbucket API
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    if not account_id:
        return {
            "status": "error",
            "error": f"Could not find account_id for '{user_email}'",
        }
    
    res = svc.remove_workspace_member(account_id, workspace)
    
    if res.get("status") == "success":
        res["user"] = display_name
        res["message"] = f"Removed '{display_name}' from workspace."
    
    logger.info(f"bitbucket_remove_workspace_member result: {res}")
    return res


# ---------- Bitbucket Repository Tools ----------

def bitbucket_list_repositories(workspace: str = None, limit: int = 50) -> dict[str, Any]:
    """
    List all repositories in a Bitbucket workspace.
    
    workspace: The workspace slug. If not provided, uses the default workspace.
    limit: Maximum number of repositories to return.
    """
    logger.info(f"bitbucket_list_repositories(workspace={workspace}, limit={limit})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.list_repositories(workspace, limit)
    logger.info(f"bitbucket_list_repositories result: {res.get('total', 0)} repos found")
    return res


def bitbucket_get_repository(repo_slug: str, workspace: str = None) -> dict[str, Any]:
    """
    Get details of a specific Bitbucket repository.
    
    repo_slug: The repository slug (e.g., "my-repo").
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_get_repository(repo_slug={repo_slug}, workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.get_repository(repo_slug, workspace)
    logger.info(f"bitbucket_get_repository result: {res}")
    return res


def bitbucket_get_repository_permissions(repo_slug: str, workspace: str = None) -> dict[str, Any]:
    """
    Get permissions for a Bitbucket repository.
    
    Shows all users and groups with their access levels (read, write, admin).
    
    repo_slug: The repository slug.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_get_repository_permissions(repo_slug={repo_slug}, workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.get_repository_permissions(repo_slug, workspace)
    logger.info(f"bitbucket_get_repository_permissions result: {res}")
    return res


def bitbucket_grant_repository_access(
    user_email: str, repo_slug: str, permission: str = "read", workspace: str = None
) -> dict[str, Any]:
    """
    Grant a user access to a Bitbucket repository.
    
    This function automatically handles workspace membership:
    - If user is already a workspace member: grants repository access
    - If user is not a workspace member: automatically invites them to the workspace first
    
    Requires Atlassian Admin API configuration (ATLASSIAN_ORG_ID and ATLASSIAN_API_KEY)
    for automatic workspace invitations.
    
    user_email: The user's email address.
    repo_slug: The repository slug.
    permission: "read", "write", or "admin".
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_grant_repository_access(user_email={user_email}, repo_slug={repo_slug}, permission={permission})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    # Resolve user - need to get their account_id for Bitbucket API
    user = svc.get_user_by_email(user_email, workspace=workspace)
    if user.get("status") != "success":
        return {
            "status": "error",
            "error": f"User '{user_email}' not found in Atlassian. They need to be invited to Atlassian first via Jira.",
            "user_not_found": True
        }
    
    # Check if user is NOT in workspace
    if user.get("not_in_workspace"):
        logger.info(f"User '{user_email}' not in workspace. Attempting automatic invitation...")
        
        # Try to automatically add user to workspace
        account_id = user.get("account_id")
        add_result = svc.add_workspace_member(account_id, workspace, user_email)
        
        if add_result.get("status") != "success":
            # If automatic invitation failed, return clear error
            error_msg = add_result.get("error", "Failed to add user to workspace")
            
            if add_result.get("needs_manual_invitation"):
                return {
                    "status": "error",
                    "error": f"User '{user_email}' is not a member of the Bitbucket workspace. "
                             f"Automatic invitation is not configured. {error_msg}",
                    "needs_workspace_membership": True,
                    "manual_url": add_result.get("manual_url")
                }
            
            return {
                "status": "error",
                "error": f"Failed to add user to workspace: {error_msg}"
            }
        
        # User was invited successfully
        if add_result.get("invited"):
            if add_result.get("requires_acceptance"):
                return {
                    "status": "success",
                    "message": f"✉️ Sent invitation to '{user_email}' for the Bitbucket workspace. "
                               f"They must check their email and accept the invitation to activate their Bitbucket access. "
                               f"Once accepted, please run this command again to grant repository access.",
                    "invited": True,
                    "requires_user_action": True,
                    "next_steps": f"1. User checks email for Bitbucket invitation\n2. User accepts the invitation\n3. Run: bitbucket_grant_repository_access('{user_email}', '{repo_slug}', '{permission}')"
                }
            
            return {
                "status": "success",
                "message": f"Invited '{user_email}' to the Bitbucket workspace. "
                           f"They will receive an email invitation. "
                           f"Repository access will be granted automatically once they accept.",
                "invited": True
            }
        
        # User was already in org and was granted workspace access
        logger.info(f"User added to workspace. Now granting repository access...")
    
    # Use account_id for Bitbucket repository permissions API
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    if not account_id:
        return {
            "status": "error",
            "error": f"Could not resolve account_id for '{user_email}'",
        }
    
    res = svc.add_repository_permission(repo_slug, account_id, permission, workspace)
    
    if res.get("status") == "success":
        res["user"] = display_name
        res["message"] = f"Granted {permission} access to '{display_name}' for repository '{repo_slug}'."
    
    logger.info(f"bitbucket_grant_repository_access result: {res}")
    return res


def bitbucket_revoke_repository_access(
    user_email: str, repo_slug: str, workspace: str = None
) -> dict[str, Any]:
    """
    Revoke a user's access from a Bitbucket repository.
    
    user_email: The user's email address.
    repo_slug: The repository slug.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_revoke_repository_access(user_email={user_email}, repo_slug={repo_slug})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    # Resolve user - pass workspace to search in workspace members
    user = svc.get_user_by_email(user_email, workspace)
    if user.get("status") != "success":
        return user
    
    # Use account_id for Bitbucket repository permissions API
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    if not account_id:
        return {
            "status": "error",
            "error": f"Could not find account_id for '{user_email}'",
        }
    
    res = svc.remove_repository_permission(repo_slug, account_id, workspace)
    
    if res.get("status") == "success":
        res["user"] = display_name
        res["message"] = f"Revoked access for '{display_name}' from repository '{repo_slug}'."
    
    logger.info(f"bitbucket_revoke_repository_access result: {res}")
    return res


def bitbucket_add_group_to_repository(
    group_slug: str, repo_slug: str, permission: str = "read", workspace: str = None
) -> dict[str, Any]:
    """
    Grant a group access to a Bitbucket repository.
    
    group_slug: The group slug.
    repo_slug: The repository slug.
    permission: "read", "write", or "admin".
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_add_group_to_repository(group_slug={group_slug}, repo_slug={repo_slug}, permission={permission})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.add_group_to_repository(repo_slug, group_slug, permission, workspace)
    logger.info(f"bitbucket_add_group_to_repository result: {res}")
    return res


def bitbucket_remove_group_from_repository(
    group_slug: str, repo_slug: str, workspace: str = None
) -> dict[str, Any]:
    """
    Remove a group's access from a Bitbucket repository.
    
    group_slug: The group slug.
    repo_slug: The repository slug.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_remove_group_from_repository(group_slug={group_slug}, repo_slug={repo_slug})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.remove_group_from_repository(repo_slug, group_slug, workspace)
    logger.info(f"bitbucket_remove_group_from_repository result: {res}")
    return res


def bitbucket_list_user_access(user_email: str, workspace: str = None) -> dict[str, Any]:
    """
    List all Bitbucket repositories a user has explicit access to.
    
    user_email: The user's email address.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_list_user_access(user_email={user_email}, workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    # Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    res = svc.get_user_repository_access(account_id, workspace)
    
    if res.get("status") == "success":
        res["user_email"] = user_email
        res["display_name"] = display_name
        repos = res.get("repositories", [])
        if repos:
            res["message"] = f"'{display_name}' has access to {len(repos)} repository(ies)."
        else:
            res["message"] = f"'{display_name}' has no explicit repository access."
    
    logger.info(f"bitbucket_list_user_access result: {res}")
    return res


# ---------- Bitbucket Group Tools ----------

def bitbucket_list_groups(workspace: str = None) -> dict[str, Any]:
    """
    List all groups in a Bitbucket workspace.
    
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_list_groups(workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.list_groups(workspace)
    logger.info(f"bitbucket_list_groups result: {res}")
    return res


def bitbucket_get_group_members(group_slug: str, workspace: str = None) -> dict[str, Any]:
    """
    Get members of a Bitbucket workspace group.
    
    group_slug: The group slug.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_get_group_members(group_slug={group_slug}, workspace={workspace})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    res = svc.get_group_members(group_slug, workspace)
    logger.info(f"bitbucket_get_group_members result: {res}")
    return res


def bitbucket_add_user_to_group(
    user_email: str, group_slug: str, workspace: str = None
) -> dict[str, Any]:
    """
    Add a user to a Bitbucket workspace group.
    
    user_email: The user's email address.
    group_slug: The group slug.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_add_user_to_group(user_email={user_email}, group_slug={group_slug})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    # Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    res = svc.add_user_to_group(account_id, group_slug, workspace)
    
    if res.get("status") == "success":
        res["user"] = display_name
        res["message"] = f"Added '{display_name}' to group '{group_slug}'."
    
    logger.info(f"bitbucket_add_user_to_group result: {res}")
    return res


def bitbucket_remove_user_from_group(
    user_email: str, group_slug: str, workspace: str = None
) -> dict[str, Any]:
    """
    Remove a user from a Bitbucket workspace group.
    
    user_email: The user's email address.
    group_slug: The group slug.
    workspace: The workspace slug. If not provided, uses the default workspace.
    """
    logger.info(f"bitbucket_remove_user_from_group(user_email={user_email}, group_slug={group_slug})")
    svc = get_bitbucket_service()
    if not svc._session.auth:
        return {"status": "skipped", "message": "Bitbucket not configured."}
    
    # Resolve user
    user = svc.get_user_by_email(user_email)
    if user.get("status") != "success":
        return user
    
    account_id = user.get("account_id")
    display_name = user.get("display_name", user_email)
    
    res = svc.remove_user_from_group(account_id, group_slug, workspace)
    
    if res.get("status") == "success":
        res["user"] = display_name
        res["message"] = f"Removed '{display_name}' from group '{group_slug}'."
    
    logger.info(f"bitbucket_remove_user_from_group result: {res}")
    return res
