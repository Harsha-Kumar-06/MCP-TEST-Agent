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

For automatic workspace invitations (recommended):
- ATLASSIAN_ORG_ID: Your organization ID from admin.atlassian.com
- ATLASSIAN_API_KEY: API key created at admin.atlassian.com
"""
from __future__ import annotations
import os
import logging
import requests
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


class AtlassianAdminService:
    """Client for Atlassian Admin/Organization REST API for managing workspace membership."""

    def __init__(self) -> None:
        self.base_url = "https://api.atlassian.com/admin"
        self.org_id = os.getenv("ATLASSIAN_ORG_ID")
        self.api_key = os.getenv("ATLASSIAN_API_KEY")
        
        self._session = requests.Session()
        
        if self.api_key:
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            })
        else:
            logger.warning(
                "Atlassian Admin API not configured. "
                "Set ATLASSIAN_ORG_ID and ATLASSIAN_API_KEY to enable automatic workspace invitations. "
                "Create an API key at: https://admin.atlassian.com/o/{org}/settings/api-keys"
            )
    
    def is_configured(self) -> bool:
        """Check if the Admin API is properly configured."""
        return bool(self.org_id and self.api_key)
    
    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _request(
        self, method: str, path: str, json: Optional[dict] = None, params: Optional[dict] = None
    ) -> tuple[Optional[Union[dict, list]], Optional[str]]:
        if not self.is_configured():
            return None, "Atlassian Admin API not configured"
        try:
            logger.debug(f"Admin API {method} {path} json={json} params={params}")
            r = self._session.request(
                method, self._url(path), json=json, params=params, timeout=30
            )
            r.raise_for_status()
            return r.json() if r.text else {}, None
        except requests.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                    if 'message' in error_body:
                        error_msg = error_body['message']
                    elif 'error' in error_body:
                        error_msg = error_body['error']
                except Exception:
                    pass
            logger.error(f"Admin API error: {error_msg}")
            return None, error_msg

    def get_workspaces(self) -> dict[str, Any]:
        """Get all Bitbucket workspaces in the organization."""
        data, err = self._request(
            "POST",
            f"v2/orgs/{self.org_id}/workspaces",
            json={"limit": 100}
        )
        
        if err:
            return {"status": "error", "error": err}
        
        workspaces = []
        for item in data.get("data", []):
            attrs = item.get("attributes", {})
            # Filter for Bitbucket workspaces
            if attrs.get("typeKey") == "bitbucket":
                # Extract slug from URL (e.g., https://bitbucket.org/thetestmusa/ -> thetestmusa)
                url = attrs.get("hostUrl", "")
                slug = None
                if url:
                    # URL format: https://bitbucket.org/{workspace}/
                    parts = url.rstrip('/').split('/')
                    if len(parts) >= 4 and parts[-2] == 'bitbucket.org':
                        slug = parts[-1]
                    elif len(parts) >= 1:
                        slug = parts[-1]
                
                # Fallback to name if URL parsing fails
                if not slug:
                    slug = attrs.get("name", "").lower()
                
                workspaces.append({
                    "id": item.get("id"),
                    "name": attrs.get("name"),
                    "slug": slug,
                    "url": url,
                })
                logger.info(f"Found Bitbucket workspace: id={item.get('id')}, name={attrs.get('name')}, slug={slug}")
        
        logger.info(f"Total Bitbucket workspaces found: {len(workspaces)}")
        return {
            "status": "success",
            "workspaces": workspaces
        }
    
    def get_workspace_ari(self, workspace_slug: str) -> dict[str, Any]:
        """Get the ARI (Atlassian Resource Identifier) for a Bitbucket workspace."""
        result = self.get_workspaces()
        if result.get("status") != "success":
            return result
        
        workspaces = result.get("workspaces", [])
        logger.info(f"Looking for workspace slug '{workspace_slug}' among {len(workspaces)} workspaces")
        
        # Try exact match first
        for ws in workspaces:
            logger.debug(f"Checking workspace: {ws}")
            if ws.get("slug") == workspace_slug:
                workspace_id = ws.get("id")
                logger.info(f"Found exact match: workspace_id={workspace_id}")
                # workspace_id already contains full ARI from Admin API
                return {
                    "status": "success",
                    "ari": workspace_id,
                    "workspace_id": workspace_id
                }
        
        # Try case-insensitive match
        workspace_slug_lower = workspace_slug.lower()
        for ws in workspaces:
            if ws.get("slug", "").lower() == workspace_slug_lower:
                workspace_id = ws.get("id")
                logger.info(f"Found case-insensitive match: workspace_id={workspace_id}")
                # workspace_id already contains full ARI from Admin API
                return {
                    "status": "success",
                    "ari": workspace_id,
                    "workspace_id": workspace_id
                }
        
        # No match found - return detailed error
        available_slugs = [ws.get("slug") for ws in workspaces]
        logger.error(f"Workspace '{workspace_slug}' not found. Available: {available_slugs}")
        return {
            "status": "error",
            "error": f"Workspace '{workspace_slug}' not found in organization. Available workspaces: {', '.join(available_slugs) if available_slugs else 'none'}",
            "available_workspaces": available_slugs
        }
    
    def invite_user_to_product(self, email: str, resource_ari: str) -> dict[str, Any]:
        """Invite a user to the organization and grant them access to a product (e.g., Bitbucket workspace).
        
        Args:
            email: User's email address
            resource_ari: ARI of the resource (e.g., ari:cloud:bitbucket::{workspace_id})
        """
        logger.info(f"Inviting {email} to product {resource_ari}")
        
        payload = {
            "emails": [email],  # Note: API expects "emails" (plural)
            "permissionRules": [
                {
                    "resource": resource_ari,
                    "role": "atlassian/user"
                }
            ],
            "sendNotification": True,
            "notificationText": "You've been granted access to our Bitbucket workspace."
        }
        logger.info(f"Invite payload: {payload}")
        
        data, err = self._request(
            "POST",
            f"v2/orgs/{self.org_id}/users/invite",
            json=payload
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Invited {email} to product. They will receive an email invitation.",
            "data": data
        }
    
    def grant_user_product_access(self, account_id: str, resource_ari: str) -> dict[str, Any]:
        """Grant an existing organization user access to a product.
        
        Args:
            account_id: User's Atlassian account ID
            resource_ari: ARI of the resource (e.g., ari:cloud:bitbucket::{workspace_id})
        """
        logger.info(f"Granting user {account_id} access to {resource_ari}")
        
        data, err = self._request(
            "POST",
            f"v1/orgs/{self.org_id}/users/{account_id}/roles/assign",
            json={
                "role": "atlassian/user",
                "resource": resource_ari
            }
        )
        
        if err:
            if "not found" in str(err).lower():
                return {
                    "status": "error",
                    "error": f"User {account_id} not found in organization",
                    "user_not_found": True
                }
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Granted user access to product"
        }


# Singleton for admin service
_admin_service: Optional[AtlassianAdminService] = None


def get_atlassian_admin_service() -> Optional[AtlassianAdminService]:
    """Get or create the Atlassian Admin service singleton."""
    global _admin_service
    if _admin_service is None:
        _admin_service = AtlassianAdminService()
    return _admin_service if _admin_service.is_configured() else None


class BitbucketService:
    """Client for Bitbucket Cloud REST API 2.0 for repository and workspace access management."""

    def __init__(self) -> None:
        self.base_url = "https://api.bitbucket.org/2.0"
        
        # Bitbucket-specific credentials are now OPTIONAL
        # Primary method for user management is Atlassian Organization Admin API
        self.email = os.getenv("BITBUCKET_USERNAME") or os.getenv("JIRA_EMAIL")
        self.api_token = (
            os.getenv("BITBUCKET_API_TOKEN") or 
            os.getenv("BITBUCKET_APP_PASSWORD")  # Legacy support
        )
        
        # Note: Bitbucket API token is only needed for repository-level permissions
        # User invitations and workspace access are handled by Admin API
        if not self.api_token:
            logger.info(
                "No Bitbucket API token configured. Using Atlassian Admin API for user management. "
                "Repository-level permissions will require manual configuration or a Bitbucket API token."
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
        self, account_id: str, workspace: Optional[str] = None, user_email: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Add a user to a workspace using Atlassian Admin API.
        
        This method automatically invites users to the Bitbucket workspace if they don't
        have access. It uses the Atlassian Organization Admin API to manage workspace membership.
        
        Args:
            account_id: User's Atlassian account ID (format: 557058:xxx or 712020:xxx)
            workspace: The workspace slug (optional, uses default if not provided)
            user_email: User's email address (required for invitation if user not in workspace)
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Adding user {account_id} to workspace {ws} via Atlassian Admin API")
        
        # Try to use Atlassian Admin API for automatic invitation
        admin_service = get_atlassian_admin_service()
        if not admin_service:
            return {
                "status": "error",
                "error": "Atlassian Admin API not configured. Set ATLASSIAN_ORG_ID and ATLASSIAN_API_KEY to enable automatic workspace invitations. "
                         "Alternatively, invite the user manually at https://admin.atlassian.com",
                "needs_manual_invitation": True,
                "manual_url": "https://admin.atlassian.com"
            }
        
        # Get workspace ARI
        workspace_ari_result = admin_service.get_workspace_ari(ws)
        if workspace_ari_result.get("status") != "success":
            return workspace_ari_result
        
        workspace_ari = workspace_ari_result.get("ari")
        
        # For Bitbucket, always use invite endpoint to ensure user gets email and activates product
        # The grant_user_product_access endpoint succeeds but doesn't activate the user in Bitbucket
        if not user_email:
            return {
                "status": "error",
                "error": f"User email required for Bitbucket workspace invitation"
            }
        
        logger.info(f"Inviting {user_email} (account_id: {account_id}) to workspace {ws}")
        invite_result = admin_service.invite_user_to_product(user_email, workspace_ari)
        
        if invite_result.get("status") == "success":
            return {
                "status": "success",
                "message": f"Invited {user_email} to workspace {ws}. They will receive an email invitation and must accept it to gain access.",
                "invited": True,
                "requires_acceptance": True
            }
        return invite_result

    def remove_workspace_member(
        self, account_id: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Remove a user from a workspace.
        
        Args:
            account_id: User's Atlassian account ID (format: 557058:xxx or 712020:xxx)
            workspace: The workspace slug (optional, uses default if not provided)
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Removing user {account_id} from workspace {ws}")
        
        _, err = self._request(
            "DELETE",
            f"workspaces/{ws}/permissions/users/{account_id}"
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
        
        IMPORTANT: The user MUST already be a workspace member!
        Workspace membership in Bitbucket Cloud is managed via admin.atlassian.com.
        
        account_id: The user's Atlassian account ID (format: 557058:xxx or 712020:xxx)
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
            # Check for common errors
            if "must be a member" in str(err).lower() or "not a member" in str(err).lower():
                return {
                    "status": "error",
                    "error": f"User is not a workspace member. In Bitbucket Cloud, workspace membership is managed via admin.atlassian.com. Please invite the user to the workspace through the Atlassian Admin console first.",
                    "needs_workspace_membership": True
                }
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Granted {permission} access to repository {ws}/{repo_slug}",
            "permission": permission,
        }

    def remove_repository_permission(
        self, repo_slug: str, account_id: str, workspace: Optional[str] = None
    ) -> dict[str, Any]:
        """Remove a user's permission from a repository.
        
        Args:
            repo_slug: The repository slug
            account_id: User's Atlassian account ID (format: 557058:xxx or 712020:xxx)
            workspace: The workspace slug (optional, uses default if not provided)
        """
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

    def get_user_by_email(self, email: str, workspace: Optional[str] = None) -> dict[str, Any]:
        """
        Find a Bitbucket user by email.
        
        Bitbucket doesn't have a direct user search API, so we:
        1. First check workspace members for the user
        2. Fall back to Atlassian user directory lookup
        
        Important: Bitbucket uses UUIDs like {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}
        NOT Atlassian account IDs like 712020:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
        """
        ws = workspace or self.default_workspace
        
        # First, try to find user in workspace members
        if ws:
            members_result = self.get_workspace_members(workspace=ws)
            if members_result.get("status") == "success":
                for member in members_result.get("members", []):
                    # Check by display name containing email or nickname
                    display_name = member.get("display_name", "").lower()
                    nickname = member.get("nickname", "").lower()
                    email_lower = email.lower()
                    
                    # Bitbucket doesn't always expose email, so check name/nickname
                    if email_lower in display_name or email_lower.split("@")[0] in nickname:
                        return {
                            "status": "success",
                            "uuid": member.get("uuid"),  # This is what Bitbucket API needs
                            "account_id": member.get("account_id"),
                            "display_name": member.get("display_name"),
                            "email": email,
                            "source": "workspace_members"
                        }
        
        # If not found in workspace, user may need to be invited
        # Try Atlassian user lookup as fallback (to get account_id for invitation)
        from .jira_service import get_jira_service
        jira = get_jira_service()
        jira_result = jira.get_user_by_email(email)
        
        if jira_result.get("status") == "success":
            # User exists in Atlassian but not in Bitbucket workspace
            return {
                "status": "success",
                "account_id": jira_result.get("account_id"),
                "display_name": jira_result.get("display_name"),
                "email": email,
                "not_in_workspace": True,
                "source": "atlassian_directory",
                "message": f"User found in Atlassian but not in Bitbucket workspace '{ws}'. They need to be added to the workspace first."
            }
        
        return {
            "status": "error",
            "error": f"User '{email}' not found in Atlassian. They need to be invited first.",
            "user_not_found": True
        }

    def search_user_in_workspace(self, email: str, workspace: Optional[str] = None) -> dict[str, Any]:
        """
        Search for a user in a workspace by email.
        Returns the user's UUID if found.
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        # Get workspace members and search
        members_result = self.get_workspace_members(workspace=ws)
        if members_result.get("status") != "success":
            return members_result
        
        email_lower = email.lower()
        username_part = email_lower.split("@")[0]
        
        for member in members_result.get("members", []):
            display_name = (member.get("display_name") or "").lower()
            nickname = (member.get("nickname") or "").lower()
            
            # Check if email username matches nickname or is in display name
            if username_part == nickname or username_part in display_name or email_lower in display_name:
                return {
                    "status": "success",
                    "uuid": member.get("uuid"),
                    "account_id": member.get("account_id"),
                    "display_name": member.get("display_name"),
                    "nickname": member.get("nickname"),
                }
        
        return {
            "status": "error",
            "error": f"User '{email}' not found in workspace '{ws}'",
            "user_not_found": True
        }

    def invite_user_to_workspace(
        self, email: str, workspace: Optional[str] = None, permission: str = "member"
    ) -> dict[str, Any]:
        """
        Invite a user to a Bitbucket workspace.
        
        The user must have an Atlassian account first.
        """
        ws = workspace or self.default_workspace
        if not ws:
            return {"status": "error", "error": "No workspace specified"}
        
        logger.info(f"Inviting user {email} to workspace {ws}")
        
        # First, get the user's Atlassian account ID
        from .jira_service import get_jira_service
        jira = get_jira_service()
        jira_result = jira.get_user_by_email(email)
        
        if jira_result.get("status") != "success":
            return {
                "status": "error",
                "error": f"User '{email}' not found in Atlassian. Invite them to Jira first.",
                "user_not_found": True
            }
        
        account_id = jira_result.get("account_id")
        display_name = jira_result.get("display_name", email)
        
        # Add user to workspace
        data, err = self._request(
            "PUT",
            f"workspaces/{ws}/permissions/users/{account_id}",
            json={"permission": permission}
        )
        
        if err:
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Invited '{display_name}' ({email}) to workspace '{ws}'",
            "user": display_name,
            "workspace": ws,
            "permission": permission
        }

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
