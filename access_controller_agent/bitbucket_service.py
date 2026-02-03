"""
Bitbucket Cloud REST API service for access management.
Supports: workspace permissions, repository permissions, user/group management.

IMPORTANT: Bitbucket Cloud requires a separate API token with scopes.
- The Atlassian API token from id.atlassian.com works for Jira and Confluence
- Bitbucket Cloud requires an API token created at:
  https://bitbucket.org/account/settings/api-tokens/

Required Environment Variables:
- BITBUCKET_USERNAME: Your Atlassian account email (same as JIRA_EMAIL)
- BITBUCKET_API_TOKEN: API token created in Bitbucket settings with required scopes
- BITBUCKET_WORKSPACE: Your workspace slug (optional, can be derived from JIRA_BASE_URL)
"""
from __future__ import annotations
import os
import logging
import requests
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


class BitbucketService:
    """Client for Bitbucket Cloud REST API 2.0 for repository and workspace access management."""

    def __init__(self) -> None:
        self.base_url = "https://api.bitbucket.org/2.0"
        
        # Bitbucket requires its own API Token with scopes (not the Atlassian API Token)
        # Check for Bitbucket-specific credentials first, then fall back to Jira credentials
        self.email = os.getenv("BITBUCKET_USERNAME") or os.getenv("JIRA_EMAIL")
        self.api_token = (
            os.getenv("BITBUCKET_API_TOKEN") or 
            os.getenv("BITBUCKET_APP_PASSWORD")  # Legacy support
        )
        
        # If no Bitbucket token, try Jira token (will likely fail for most endpoints)
        if not self.api_token:
            self.api_token = os.getenv("JIRA_API_TOKEN")
            if self.api_token:
                logger.warning(
                    "Using JIRA_API_TOKEN for Bitbucket. This may not work! "
                    "Bitbucket Cloud requires an API token with scopes created at: "
                    "https://bitbucket.org/account/settings/api-tokens/"
                )
        
        # Workspace is typically set in env or derived from the Jira URL
        self.default_workspace = os.getenv("BITBUCKET_WORKSPACE") or self._derive_workspace()
        
        self._session = requests.Session()
        
        if self.email and self.api_token:
            self._session.auth = (self.email, self.api_token)
            self._session.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json"
            })
        else:
            logger.warning(
                "Bitbucket credentials missing. "
                "Set BITBUCKET_USERNAME and BITBUCKET_API_TOKEN. "
                "Create an API token at: https://bitbucket.org/account/settings/api-tokens/"
            )
    
    def _derive_workspace(self) -> Optional[str]:
        """Try to derive workspace from Jira URL (e.g., https://mycompany.atlassian.net -> mycompany)."""
        jira_url = os.getenv("JIRA_BASE_URL", "")
        if "atlassian.net" in jira_url:
            # Extract workspace from https://workspace.atlassian.net
            import re
            match = re.search(r"https?://([^.]+)\.atlassian\.net", jira_url)
            if match:
                return match.group(1)
        return None

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request(
        self, method: str, path: str, json: Optional[dict] = None, params: Optional[dict] = None
    ) -> tuple[Optional[Union[dict, list]], Optional[str]]:
        if not self._session.auth:
            return None, "Bitbucket not configured (missing credentials)"
        try:
            logger.debug(f"Bitbucket API {method} {path} json={json} params={params}")
            r = self._session.request(
                method, self._url(path), json=json, params=params, timeout=30
            )
            r.raise_for_status()
            return r.json() if r.text else None, None
        except requests.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                    if 'error' in error_body:
                        err = error_body['error']
                        if isinstance(err, dict):
                            error_msg = err.get('message', str(err))
                        else:
                            error_msg = str(err)
                    else:
                        error_msg = str(error_body)
                except:
                    error_msg = e.response.text or str(e)
            logger.error(f"Bitbucket request failed: {method} {path} -> {error_msg}")
            return None, error_msg

    # ==================== WORKSPACE MANAGEMENT ====================

    def list_workspaces(self) -> dict[str, Any]:
        """
        List all workspaces the authenticated user has access to.
        """
        data, err = self._request("GET", "workspaces", params={"pagelen": 100})
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No workspaces returned"}
        
        workspaces = []
        for w in data.get("values", []):
            workspaces.append({
                "slug": w.get("slug"),
                "name": w.get("name"),
                "uuid": w.get("uuid"),
                "is_private": w.get("is_private", True),
            })
        
        return {
            "status": "success",
            "workspaces": workspaces,
            "total": len(workspaces),
            "default_workspace": self.default_workspace,
        }

    def get_workspace(self, workspace: Optional[str] = None) -> dict[str, Any]:
        """Get details of a workspace."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified and no default set"}
        
        data, err = self._request("GET", f"workspaces/{ws}")
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "Workspace not found"}
        
        return {
            "status": "success",
            "workspace": {
                "slug": data.get("slug"),
                "name": data.get("name"),
                "uuid": data.get("uuid"),
                "is_private": data.get("is_private", True),
            }
        }

    def get_workspace_members(self, workspace: Optional[str] = None) -> dict[str, Any]:
        """
        Get all members of a workspace.
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        data, err = self._request("GET", f"workspaces/{ws}/members", params={"pagelen": 100})
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No members returned"}
        
        members = []
        for m in data.get("values", []):
            user = m.get("user", {})
            members.append({
                "account_id": user.get("account_id"),
                "uuid": user.get("uuid"),
                "display_name": user.get("display_name"),
                "nickname": user.get("nickname"),
            })
        
        return {
            "status": "success",
            "workspace": ws,
            "members": members,
            "total": len(members),
        }

    def add_workspace_member(
        self, account_id: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Add a user to a workspace.
        Note: User must already have an Atlassian account.
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Adding user {account_id} to workspace {ws}")
        
        # Bitbucket uses workspace permissions endpoint
        data, err = self._request(
            "PUT",
            f"workspaces/{ws}/permissions/user/{account_id}",
            json={"permission": "member"}
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Added user to workspace {ws}",
        }

    def remove_workspace_member(
        self, account_id: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Remove a user from a workspace."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Removing user {account_id} from workspace {ws}")
        
        _, err = self._request(
            "DELETE",
            f"workspaces/{ws}/permissions/user/{account_id}"
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Removed user from workspace {ws}",
        }

    # ==================== REPOSITORY MANAGEMENT ====================

    def list_repositories(self, workspace: Optional[str] = None, limit: int = 50) -> dict[str, Any]:
        """
        List all repositories in a workspace.
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        data, err = self._request(
            "GET", 
            f"repositories/{ws}",
            params={"pagelen": limit}
        )
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No repositories returned"}
        
        repos = []
        for r in data.get("values", []):
            repos.append({
                "slug": r.get("slug"),
                "name": r.get("name"),
                "uuid": r.get("uuid"),
                "full_name": r.get("full_name"),
                "is_private": r.get("is_private", True),
                "project": r.get("project", {}).get("name"),
            })
        
        return {
            "status": "success",
            "workspace": ws,
            "repositories": repos,
            "total": len(repos),
        }

    def get_repository(self, repo_slug: str, workspace: Optional[str] = None) -> dict[str, Any]:
        """Get details of a specific repository."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        data, err = self._request("GET", f"repositories/{ws}/{repo_slug}")
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "Repository not found"}
        
        return {
            "status": "success",
            "repository": {
                "slug": data.get("slug"),
                "name": data.get("name"),
                "uuid": data.get("uuid"),
                "full_name": data.get("full_name"),
                "is_private": data.get("is_private", True),
                "project": data.get("project", {}).get("name"),
                "description": data.get("description"),
            }
        }

    def get_repository_permissions(
        self, repo_slug: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get permissions for a repository.
        Returns users and groups with their access levels.
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        # Get user permissions
        user_data, err = self._request(
            "GET",
            f"repositories/{ws}/{repo_slug}/permissions-config/users",
            params={"pagelen": 100}
        )
        
        user_permissions = []
        if not err and user_data:
            for p in user_data.get("values", []):
                user = p.get("user", {})
                user_permissions.append({
                    "account_id": user.get("account_id"),
                    "uuid": user.get("uuid"),
                    "display_name": user.get("display_name"),
                    "permission": p.get("permission"),
                })
        
        # Get group permissions
        group_data, err = self._request(
            "GET",
            f"repositories/{ws}/{repo_slug}/permissions-config/groups",
            params={"pagelen": 100}
        )
        
        group_permissions = []
        if not err and group_data:
            for p in group_data.get("values", []):
                group = p.get("group", {})
                group_permissions.append({
                    "group_slug": group.get("slug"),
                    "group_name": group.get("name"),
                    "permission": p.get("permission"),
                })
        
        return {
            "status": "success",
            "repository": f"{ws}/{repo_slug}",
            "user_permissions": user_permissions,
            "group_permissions": group_permissions,
        }

    def add_repository_permission(
        self, repo_slug: str, account_id: str, permission: str = "read",
        workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Grant a user permission to a repository.
        
        permission options:
        - "read" - Read access
        - "write" - Read + Write access
        - "admin" - Full admin access
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Adding {permission} permission for user {account_id} to repo {ws}/{repo_slug}")
        
        data, err = self._request(
            "PUT",
            f"repositories/{ws}/{repo_slug}/permissions-config/users/{account_id}",
            json={"permission": permission}
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Granted {permission} access to repository {ws}/{repo_slug}",
            "permission": permission,
        }

    def remove_repository_permission(
        self, repo_slug: str, account_id: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Remove a user's permission from a repository."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Removing user {account_id} from repo {ws}/{repo_slug}")
        
        _, err = self._request(
            "DELETE",
            f"repositories/{ws}/{repo_slug}/permissions-config/users/{account_id}"
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Removed access from repository {ws}/{repo_slug}",
        }

    def add_group_to_repository(
        self, repo_slug: str, group_slug: str, permission: str = "read",
        workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Grant a group permission to a repository."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Adding {permission} permission for group {group_slug} to repo {ws}/{repo_slug}")
        
        data, err = self._request(
            "PUT",
            f"repositories/{ws}/{repo_slug}/permissions-config/groups/{group_slug}",
            json={"permission": permission}
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Granted {permission} access to group {group_slug} for repository {ws}/{repo_slug}",
        }

    def remove_group_from_repository(
        self, repo_slug: str, group_slug: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Remove a group's permission from a repository."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        _, err = self._request(
            "DELETE",
            f"repositories/{ws}/{repo_slug}/permissions-config/groups/{group_slug}"
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Removed group {group_slug} access from repository {ws}/{repo_slug}",
        }

    # ==================== USER MANAGEMENT ====================

    def get_user_by_email(self, email: str) -> dict[str, Any]:
        """
        Find a Bitbucket user by email.
        Note: Uses Atlassian user directory (same as Jira/Confluence).
        """
        # Bitbucket doesn't have direct email search, use Jira's user search
        from .jira_service import get_jira_service
        jira = get_jira_service()
        return jira.get_user_by_email(email)

    def get_user_repository_access(
        self, account_id: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Get all repositories a user has explicit access to.
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        # Get all repos and check each for user permissions
        repos_resp = self.list_repositories(workspace=ws, limit=100)
        if repos_resp.get("status") != "success":
            return repos_resp
        
        user_repos = []
        
        for repo in repos_resp.get("repositories", []):
            perms = self.get_repository_permissions(repo["slug"], workspace=ws)
            if perms.get("status") == "success":
                for up in perms.get("user_permissions", []):
                    if up.get("account_id") == account_id:
                        user_repos.append({
                            "repository": repo["slug"],
                            "full_name": repo["full_name"],
                            "permission": up.get("permission"),
                        })
                        break
        
        return {
            "status": "success",
            "workspace": ws,
            "account_id": account_id,
            "repositories": user_repos,
            "total": len(user_repos),
        }

    # ==================== GROUP MANAGEMENT ====================

    def list_groups(self, workspace: Optional[str] = None) -> dict[str, Any]:
        """List all groups in a workspace."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        data, err = self._request(
            "GET",
            f"workspaces/{ws}/permissions/groups",
            params={"pagelen": 100}
        )
        
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No groups returned"}
        
        groups = []
        for g in data.get("values", []):
            group = g.get("group", {})
            groups.append({
                "slug": group.get("slug"),
                "name": group.get("name"),
                "permission": g.get("permission"),
            })
        
        return {
            "status": "success",
            "workspace": ws,
            "groups": groups,
            "total": len(groups),
        }

    def get_group_members(
        self, group_slug: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Get members of a workspace group."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        data, err = self._request(
            "GET",
            f"workspaces/{ws}/permissions/groups/{group_slug}/members",
            params={"pagelen": 100}
        )
        
        if err:
            return {"status": "error", "error": err}
        
        members = []
        if data:
            for m in data.get("values", []):
                user = m.get("user", {}) if isinstance(m, dict) else {}
                members.append({
                    "account_id": user.get("account_id") or m.get("account_id"),
                    "display_name": user.get("display_name") or m.get("display_name"),
                    "uuid": user.get("uuid") or m.get("uuid"),
                })
        
        return {
            "status": "success",
            "workspace": ws,
            "group_slug": group_slug,
            "members": members,
            "total": len(members),
        }

    def add_user_to_group(
        self, account_id: str, group_slug: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Add a user to a workspace group."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Adding user {account_id} to group {group_slug} in workspace {ws}")
        
        _, err = self._request(
            "PUT",
            f"workspaces/{ws}/permissions/groups/{group_slug}/members/{account_id}"
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Added user to group {group_slug}",
        }

    def remove_user_from_group(
        self, account_id: str, group_slug: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Remove a user from a workspace group."""
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Removing user {account_id} from group {group_slug} in workspace {ws}")
        
        _, err = self._request(
            "DELETE",
            f"workspaces/{ws}/permissions/groups/{group_slug}/members/{account_id}"
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Removed user from group {group_slug}",
        }


# Singleton for use by tools
_bitbucket_service: Optional[BitbucketService] = None


def get_bitbucket_service() -> BitbucketService:
    global _bitbucket_service
    if _bitbucket_service is None:
        _bitbucket_service = BitbucketService()
    return _bitbucket_service
