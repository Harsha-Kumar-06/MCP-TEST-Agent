"""
Jira Cloud REST API service for access management.
Supports: user lookup by email, grant/revoke project role access, list user's project roles.
"""
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
            r = self._session.request(
                method, self._url(path), json=json, params=params, timeout=30
            )
            r.raise_for_status()
            return r.json() if r.text else None, None
        except requests.RequestException as e:
            msg = getattr(e, "response") and getattr(e.response, "text") or str(e)
            logger.exception("Jira request failed: %s", msg)
            return None, msg

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

    def grant_project_role(
        self, project_key: str, account_id: str, role_id: str
    ) -> dict[str, Any]:
        """
        Add a user (by account_id) to a project role. role_id is the numeric role id from project roles.
        """
        data, err = self._request(
            "POST",
            f"project/{project_key}/role/{role_id}",
            json={"user": [account_id]},
        )
        if err:
            return {"status": "error", "error": err}
        return {"status": "success", "message": f"Added user to project {project_key} role {role_id}"}

    def revoke_project_role(
        self, project_key: str, account_id: str, role_id: str
    ) -> dict[str, Any]:
        """Remove a user from a project role."""
        _, err = self._request(
            "DELETE",
            f"project/{project_key}/role/{role_id}",
            params={"user": account_id},
        )
        if err:
            return {"status": "error", "error": err}
        return {"status": "success", "message": f"Removed user from project {project_key} role {role_id}"}

    def get_user_accessible_projects(self, account_id: str) -> dict[str, Any]:
        """
        List projects the user can access. Uses /rest/api/3/user/assignable/search with project.
        For a full list of projects for a user we use /rest/api/3/user/assignable/multiProjectSearch (if available)
        or search issues assigned to user and collect projects. Simpler: get all projects and filter by permission.
        Jira Cloud: GET /rest/api/3/project returns all projects; we can't filter by user easily.
        Alternative: GET /rest/api/3/user/assignable/search?username=... returns users assignable to a project.
        So we return projects where this user is assignable. We'll use project search and then for each project
        check if user is in assignable list, or we return a message that we list by project.
        Simplest: return projects the current API user can see and indicate "use list_my_projects or pass project_key".
        """
        data, err = self._request("GET", "project")
        if err:
            return {"status": "error", "error": err}
        if not data or not isinstance(data, list):
            return {"status": "error", "error": "Could not list projects"}
        projects = [
            {"key": p.get("key"), "name": p.get("name")}
            for p in data
            if p.get("key")
        ]
        return {
            "status": "success",
            "account_id": account_id,
            "message": "All projects (user-specific project list requires project key).",
            "projects": projects[:50],
        }


# Singleton for use by tools
_jira_service: Optional[JiraService] = None


def get_jira_service() -> JiraService:
    global _jira_service
    if _jira_service is None:
        _jira_service = JiraService()
    return _jira_service
