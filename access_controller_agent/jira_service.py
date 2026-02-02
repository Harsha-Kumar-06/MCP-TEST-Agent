"""
Jira Cloud REST API service for access management.
Supports: user lookup by email, grant/revoke project role access, list user's project roles.
"""
from __future__ import annotations
import os
import logging
import requests
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


class JiraService:
    """Client for Jira Cloud REST API (v3) for project role and user operations."""

    def __init__(self) -> None:
        self.base_url = (os.getenv("JIRA_BASE_URL") or "").rstrip("/")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self._session = requests.Session()
        if self.base_url and self.email and self.api_token:
            self._session.auth = (self.email, self.api_token)
            self._session.headers.update({"Accept": "application/json", "Content-Type": "application/json"})
        else:
            logger.warning(
                "Jira credentials missing (JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN). "
                "Jira tools will return mock/skip responses."
            )

    def _url(self, path: str) -> str:
        return f"{self.base_url}/rest/api/3/{path.lstrip('/')}"

    def _request(
        self, method: str, path: str, json: Optional[dict] = None, params: Optional[dict] = None
    ) -> tuple[Optional[Union[dict, list]], Optional[str]]:
        if not self.base_url or not self._session.auth:
            return None, "Jira not configured (missing URL or credentials)"
        try:
            logger.debug(f"Jira API {method} {path} json={json} params={params}")
            r = self._session.request(
                method, self._url(path), json=json, params=params, timeout=30
            )
            r.raise_for_status()
            return r.json() if r.text else None, None
        except requests.RequestException as e:
            # Extract detailed error message from Jira response
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                    # Jira returns errors in various formats
                    if 'errorMessages' in error_body:
                        error_msg = "; ".join(error_body['errorMessages'])
                    elif 'errors' in error_body:
                        error_msg = str(error_body['errors'])
                    elif 'message' in error_body:
                        error_msg = error_body['message']
                    else:
                        error_msg = str(error_body)
                except:
                    error_msg = e.response.text or str(e)
            logger.error(f"Jira request failed: {method} {path} -> {error_msg}")
            return None, error_msg

    def get_user_by_email(self, email: str) -> dict[str, Any]:
        """
        Find a Jira user by email. Returns dict with status, account_id, display_name, email.
        """
        data, err = self._request("GET", "user/search", params={"query": email})
        if err:
            return {"status": "error", "error": err}
        if not data or not isinstance(data, list):
            return {"status": "error", "error": "No user found"}
        
        # 1. Try exact email match (for users with visible email)
        for u in data:
            if (u.get("emailAddress") or "").lower() == email.lower():
                return {
                    "status": "success",
                    "account_id": u.get("accountId"),
                    "display_name": u.get("displayName"),
                    "email": u.get("emailAddress"),
                }
        
        # 2. Fallback: If we have results but no visible email matched, pick the best candidate.
        # This handles users with hidden emails in Jira profile privacy settings.
        # We assume the first result is the most relevant from Jira's search.
        if data:
            u = data[0]
            if u.get("accountId"):
                # Use provided email since the API one might be hidden/missing
                return {
                    "status": "success",
                    "account_id": u.get("accountId"),
                    "display_name": u.get("displayName"),
                    "email": u.get("emailAddress") or email,
                    "note": "Email matched via search query (hidden in profile)."
                }

        return {"status": "error", "error": f"No user found with email: {email}"}

    def invite_user(self, email: str) -> dict[str, Any]:
        """
        Invite a user to Jira by email. Creates an invitation for the user.
        The user will receive an email invitation to join the Jira site.
        """
        logger.info(f"Inviting user with email: {email}")
        
        # Jira Cloud API to create/invite a user
        # POST /rest/api/3/user with emailAddress
        data, err = self._request(
            "POST",
            "user",
            json={
                "emailAddress": email,
                "products": []  # Empty array means access to Jira only (not Confluence, etc.)
            }
        )
        
        if err:
            # Check if the error indicates user already exists
            if "already exists" in str(err).lower() or "already has access" in str(err).lower():
                return {
                    "status": "error",
                    "error": f"User with email {email} already exists in Jira. Try searching for them.",
                    "already_exists": True
                }
            return {"status": "error", "error": err}
        
        if data:
            return {
                "status": "success",
                "message": f"Invitation sent to {email}. The user will receive an email to join Jira.",
                "account_id": data.get("accountId"),
                "email": email
            }
        
        return {
            "status": "success",
            "message": f"Invitation sent to {email}. The user will receive an email to join Jira."
        }

    def get_project_roles(self, project_key: str) -> dict[str, Any]:
        """
        Get role id -> name map for a project. Returns dict with status and roles {id: name}.
        """
        data, err = self._request("GET", f"project/{project_key}/role")
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No roles returned"}
        roles = {}
        for role_name, role_url in (data or {}).items():
            if isinstance(role_url, str) and "/role/" in role_url:
                role_id = role_url.rstrip("/").split("/role/")[-1]
                roles[role_id] = role_name
        return {"status": "success", "roles": roles}

    def get_role_members(self, project_key: str, role_id: str) -> dict[str, Any]:
        """
        Get all actors (users/groups) assigned to a specific project role.
        Returns list of account IDs in that role.
        """
        data, err = self._request("GET", f"project/{project_key}/role/{role_id}")
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No role data returned"}
        
        actors = data.get("actors", [])
        members = []
        for actor in actors:
            if actor.get("actorUser"):
                members.append({
                    "account_id": actor.get("actorUser", {}).get("accountId"),
                    "display_name": actor.get("displayName"),
                    "type": "user"
                })
            elif actor.get("actorGroup"):
                members.append({
                    "name": actor.get("actorGroup", {}).get("name") or actor.get("displayName"),
                    "type": "group"
                })
        return {"status": "success", "role_id": role_id, "members": members}

    def is_user_in_role(self, project_key: str, role_id: str, account_id: str) -> bool:
        """Check if a user (by account_id) is already in the specified project role."""
        result = self.get_role_members(project_key, role_id)
        if result.get("status") != "success":
            return False
        for member in result.get("members", []):
            if member.get("type") == "user" and member.get("account_id") == account_id:
                return True
        return False

    def get_user_roles_in_project(self, project_key: str, account_id: str) -> dict[str, Any]:
        """
        Get all roles a user has in a specific project.
        """
        roles_resp = self.get_project_roles(project_key)
        if roles_resp.get("status") != "success":
            return roles_resp
        
        user_roles = []
        for role_id, role_name in roles_resp.get("roles", {}).items():
            if self.is_user_in_role(project_key, role_id, account_id):
                user_roles.append({"role_id": role_id, "role_name": role_name})
        
        return {
            "status": "success",
            "project_key": project_key,
            "account_id": account_id,
            "roles": user_roles
        }

    def grant_project_role(
        self, project_key: str, account_id: str, role_id: str
    ) -> dict[str, Any]:
        """
        Add a user (by account_id) to a project role. role_id is the numeric role id from project roles.
        Uses Jira Cloud REST API v3 format.
        """
        logger.info(f"Granting role {role_id} to account {account_id} in project {project_key}")
        
        # Jira Cloud REST API v3 expects user account IDs in the 'user' array
        # But some Jira instances use 'accountId' key instead
        # Try the standard format first
        data, err = self._request(
            "POST",
            f"project/{project_key}/role/{role_id}",
            json={"user": [account_id]},
        )
        
        # If that fails, try the accountId format (some Jira Cloud instances)
        if err:
            logger.info(f"Standard format failed, trying accountId format...")
            data, err2 = self._request(
                "POST",
                f"project/{project_key}/role/{role_id}",
                json={"accountId": [account_id]},
            )
            if not err2:
                err = None  # Success with alternate format
            else:
                # Return the original error as it's more informative
                logger.error(f"Both formats failed. Original: {err}, Alt: {err2}")
        
        if err:
            return {"status": "error", "error": err}
        
        logger.info(f"Successfully granted role. Response: {data}")
        return {"status": "success", "message": f"Added user to project {project_key} role {role_id}", "data": data}

    def revoke_project_role(
        self, project_key: str, account_id: str, role_id: str
    ) -> dict[str, Any]:
        """Remove a user from a project role using Jira Cloud REST API v3."""
        logger.info(f"Revoking role {role_id} from account {account_id} in project {project_key}")
        
        # Jira Cloud REST API v3 uses 'user' parameter for account IDs
        # But some instances require 'accountId' parameter
        _, err = self._request(
            "DELETE",
            f"project/{project_key}/role/{role_id}",
            params={"user": account_id},
        )
        
        # If that fails, try with accountId parameter
        if err:
            logger.info(f"Standard format failed, trying accountId parameter...")
            _, err2 = self._request(
                "DELETE",
                f"project/{project_key}/role/{role_id}",
                params={"accountId": account_id},
            )
            if not err2:
                err = None
            else:
                logger.error(f"Both formats failed. Original: {err}, Alt: {err2}")
        
        if err:
            return {"status": "error", "error": err}
        
        logger.info(f"Successfully revoked role from user.")
        return {"status": "success", "message": f"Removed user from project {project_key} role {role_id}"}

    def get_user_accessible_projects(self, account_id: str) -> dict[str, Any]:
        """
        List projects the user can access.
        Iterates over all projects and checks if the user has any role in each project.
        """
        # 1. Get all projects
        data, err = self._request("GET", "project")
        if err:
            return {"status": "error", "error": err}
        if not data or not isinstance(data, list):
            return {"status": "error", "error": "Could not list projects"}
        
        all_projects = [
            {"key": p.get("key"), "name": p.get("name"), "id": p.get("id")}
            for p in data
            if p.get("key")
        ]
        
        user_projects = []
        
        # 2. For each project, check if user has any role by checking role membership
        # This is more reliable than the permissions endpoint which returns unexpected data
        for p in all_projects:
            project_key = p["key"]
            
            # Get all roles for this project
            roles_resp = self.get_project_roles(project_key)
            if roles_resp.get("status") != "success":
                continue
            
            roles = roles_resp.get("roles", {})
            user_roles_in_project = []
            
            # Check each role to see if user is a member
            for role_id, role_name in roles.items():
                # Skip the atlassian-addons role as it's for apps, not users
                if role_name == "atlassian-addons-project-access":
                    continue
                    
                if self.is_user_in_role(project_key, role_id, account_id):
                    user_roles_in_project.append(role_name)
            
            # If user has any role in this project, add to list
            if user_roles_in_project:
                user_projects.append({
                    "key": project_key,
                    "name": p.get("name"),
                    "id": p.get("id"),
                    "roles": user_roles_in_project
                })

        return {
            "status": "success",
            "account_id": account_id,
            "message": f"Found {len(user_projects)} accessible projects.",
            "projects": user_projects,
        }


# Singleton for use by tools
_jira_service: Optional[JiraService] = None


def get_jira_service() -> JiraService:
    global _jira_service
    if _jira_service is None:
        _jira_service = JiraService()
    return _jira_service
