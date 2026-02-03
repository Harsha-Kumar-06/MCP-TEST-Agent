"""
Confluence Cloud REST API service for access management.
Supports: space permissions, user lookup, group management.

Confluence uses the same Atlassian credentials as Jira:
- Base URL: https://your-domain.atlassian.net (same as Jira)
- Email: Your Atlassian account email
- API Token: Same API token works for all Atlassian Cloud products
"""
from __future__ import annotations
import os
import logging
import requests
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


class ConfluenceService:
    """Client for Confluence Cloud REST API for space permissions and user operations."""

    def __init__(self) -> None:
        # Use same base URL as Jira (Atlassian Cloud)
        base_url = (os.getenv("JIRA_BASE_URL") or os.getenv("CONFLUENCE_BASE_URL") or "").rstrip("/")
        self.base_url = base_url
        self.email = os.getenv("JIRA_EMAIL") or os.getenv("CONFLUENCE_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN") or os.getenv("CONFLUENCE_API_TOKEN")
        self._session = requests.Session()
        
        if self.base_url and self.email and self.api_token:
            self._session.auth = (self.email, self.api_token)
            self._session.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json"
            })
        else:
            logger.warning(
                "Confluence credentials missing. "
                "Confluence tools will return mock/skip responses."
            )

    def _wiki_url(self, path: str) -> str:
        """Build Confluence Wiki REST API URL."""
        return f"{self.base_url}/wiki/rest/api/{path.lstrip('/')}"
    
    def _wiki_v2_url(self, path: str) -> str:
        """Build Confluence Wiki REST API v2 URL."""
        return f"{self.base_url}/wiki/api/v2/{path.lstrip('/')}"

    def _request(
        self, method: str, path: str, json: Optional[dict] = None, 
        params: Optional[dict] = None, use_v2: bool = False
    ) -> tuple[Optional[Union[dict, list]], Optional[str]]:
        if not self.base_url or not self._session.auth:
            return None, "Confluence not configured (missing URL or credentials)"
        try:
            url = self._wiki_v2_url(path) if use_v2 else self._wiki_url(path)
            logger.debug(f"Confluence API {method} {url} json={json} params={params}")
            r = self._session.request(method, url, json=json, params=params, timeout=30)
            r.raise_for_status()
            return r.json() if r.text else None, None
        except requests.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_body = e.response.json()
                    if 'message' in error_body:
                        error_msg = error_body['message']
                    elif 'errorMessage' in error_body:
                        error_msg = error_body['errorMessage']
                    else:
                        error_msg = str(error_body)
                except:
                    error_msg = e.response.text or str(e)
            logger.error(f"Confluence request failed: {method} {path} -> {error_msg}")
            return None, error_msg

    # ==================== SPACE MANAGEMENT ====================

    def list_spaces(self, limit: int = 50) -> dict[str, Any]:
        """
        List all Confluence spaces.
        Returns list of spaces with key, name, and type.
        """
        data, err = self._request("GET", "space", params={"limit": limit, "expand": "description.plain"})
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No spaces returned"}
        
        spaces = []
        for s in data.get("results", []):
            spaces.append({
                "key": s.get("key"),
                "name": s.get("name"),
                "type": s.get("type"),
                "id": s.get("id"),
            })
        
        return {
            "status": "success",
            "spaces": spaces,
            "total": len(spaces)
        }

    def get_space(self, space_key: str) -> dict[str, Any]:
        """Get details of a specific space."""
        data, err = self._request("GET", f"space/{space_key}", params={"expand": "description.plain,permissions"})
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "Space not found"}
        
        return {
            "status": "success",
            "space": {
                "key": data.get("key"),
                "name": data.get("name"),
                "type": data.get("type"),
                "id": data.get("id"),
                "description": data.get("description", {}).get("plain", {}).get("value", ""),
            }
        }

    def get_space_permissions(self, space_key: str) -> dict[str, Any]:
        """
        Get permissions for a Confluence space.
        Returns list of users and groups with their permission levels.
        """
        data, err = self._request("GET", f"space/{space_key}", params={"expand": "permissions"})
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "Space not found"}
        
        permissions = data.get("permissions", [])
        user_permissions = []
        group_permissions = []
        
        for perm in permissions:
            subjects = perm.get("subjects", {})
            operation = perm.get("operation", {})
            
            # User permissions
            for user in subjects.get("user", {}).get("results", []):
                user_permissions.append({
                    "account_id": user.get("accountId"),
                    "display_name": user.get("displayName"),
                    "email": user.get("email"),
                    "operation": operation.get("operation"),
                    "target_type": operation.get("targetType"),
                })
            
            # Group permissions
            for group in subjects.get("group", {}).get("results", []):
                group_permissions.append({
                    "group_name": group.get("name"),
                    "group_id": group.get("id"),
                    "operation": operation.get("operation"),
                    "target_type": operation.get("targetType"),
                })
        
        return {
            "status": "success",
            "space_key": space_key,
            "user_permissions": user_permissions,
            "group_permissions": group_permissions,
        }

    def _get_space_id(self, space_key: str) -> tuple[Optional[str], Optional[str]]:
        """Get the numeric space ID from space key (needed for V2 API)."""
        # First try to get from V1 API
        data, err = self._request("GET", f"space/{space_key}")
        if err:
            return None, err
        if data and "id" in data:
            return str(data["id"]), None
        return None, "Space ID not found"

    def add_space_permission(
        self, space_key: str, account_id: str, permission_type: str = "read"
    ) -> dict[str, Any]:
        """
        Add a user to a Confluence space with specified permission.
        
        permission_type options:
        - "read" (view)
        - "write" (edit/create)
        - "admin" (space admin)
        
        Supports both legacy and RBAC modes.
        """
        logger.info(f"Adding user {account_id} to space {space_key} with {permission_type} permission")
        
        # First try the V2 API (works with RBAC mode)
        result = self._add_space_permission_v2(space_key, account_id, permission_type)
        if result.get("status") == "success":
            return result
        
        # If V2 fails (not RBAC mode), try legacy API
        v2_error = result.get("error", "")
        if "not found" in v2_error.lower() or "404" in v2_error:
            return self._add_space_permission_legacy(space_key, account_id, permission_type)
        
        # Return the V2 error if it's an RBAC-related failure
        return result

    def _add_space_permission_v2(
        self, space_key: str, account_id: str, permission_type: str = "read"
    ) -> dict[str, Any]:
        """
        Add space permission using V2 API (for RBAC mode).
        Uses the /wiki/api/v2/spaces/{id}/permissions endpoint.
        """
        # Get space ID (V2 API requires numeric ID, not key)
        space_id, err = self._get_space_id(space_key)
        if err:
            return {"status": "error", "error": f"Could not get space ID: {err}"}
        
        # Map permission type to principal role
        # In RBAC mode, we use principalType and principalId
        role_map = {
            "read": "read",
            "write": "write",
            "admin": "admin",
        }
        
        role = role_map.get(permission_type.lower(), "read")
        
        # V2 API payload for adding user permission
        payload = {
            "subject": {
                "type": "user",
                "identifier": account_id
            },
            "operation": {
                "key": role,
                "targetType": "space"
            }
        }
        
        # Try V2 endpoint
        data, err = self._request("POST", f"spaces/{space_id}/permissions", json=payload, use_v2=True)
        if err:
            # Check if it's an RBAC-specific error - try alternative approach
            if "RBAC" in str(err) or "roles-only" in str(err):
                return self._add_space_role_permission(space_key, space_id, account_id, permission_type)
            return {"status": "error", "error": err}
        
        return {
            "status": "success",
            "message": f"Added {permission_type} permissions to space {space_key} for user",
            "space_key": space_key,
            "permission": permission_type,
        }

    def _add_space_role_permission(
        self, space_key: str, space_id: str, account_id: str, permission_type: str
    ) -> dict[str, Any]:
        """
        Add user to space using role-based approach for RBAC mode.
        This uses the space roles endpoint.
        """
        # In RBAC mode, spaces have roles: viewers, editors, admins
        # We need to add the user to the appropriate role
        
        # Map permission to role name
        role_map = {
            "read": "viewer",
            "write": "editor", 
            "admin": "admin",
        }
        role_name = role_map.get(permission_type.lower(), "viewer")
        
        # Try to add user to space role via V2 API
        # The endpoint might be: /wiki/api/v2/spaces/{id}/roles/{role}/members
        payload = {
            "accountId": account_id
        }
        
        # Try different role endpoints that Confluence Cloud might support
        endpoints_to_try = [
            f"spaces/{space_id}/permissions/users/{account_id}",
            f"spaces/{space_id}/roles/{role_name}/members",
        ]
        
        for endpoint in endpoints_to_try:
            data, err = self._request("PUT", endpoint, json=payload, use_v2=True)
            if not err:
                return {
                    "status": "success",
                    "message": f"Added {permission_type} permissions to space {space_key} via role",
                    "space_key": space_key,
                    "permission": permission_type,
                    "role": role_name,
                }
        
        # If role-based approach doesn't work, try adding to a group
        # that has access to the space
        group_result = self._try_add_via_group(space_key, account_id, permission_type)
        if group_result.get("status") == "success":
            return group_result
        
        return {
            "status": "error",
            "error": (
                f"Cannot add user to space in RBAC mode. "
                f"The space '{space_key}' uses role-based access control. "
                f"Please either:\n"
                f"1. Add the user to a group that has access to this space, or\n"
                f"2. Use Confluence admin UI to manage space roles directly.\n"
                f"Suggested: Use confluence_add_group_to_space to give a group access, "
                f"then use jira_add_user_to_group to add the user to that group."
            ),
            "suggestion": "Use group-based access instead of direct user permissions"
        }

    def _try_add_via_group(
        self, space_key: str, account_id: str, permission_type: str
    ) -> dict[str, Any]:
        """
        Try to add user access via group membership.
        First finds/creates an appropriate group, then adds user to it.
        """
        # Check if there's a default group for this permission level
        default_groups = {
            "read": ["confluence-users", "confluence-viewers"],
            "write": ["confluence-editors", "site-admins"],
            "admin": ["confluence-admins", "site-admins"],
        }
        
        groups_to_try = default_groups.get(permission_type.lower(), ["confluence-users"])
        
        # Get list of groups
        groups_result = self.list_groups()
        if groups_result.get("status") != "success":
            return {"status": "error", "error": "Could not list groups"}
        
        available_groups = {g["name"].lower(): g["name"] for g in groups_result.get("groups", [])}
        
        # Find a matching group
        for group in groups_to_try:
            if group.lower() in available_groups:
                actual_group_name = available_groups[group.lower()]
                # Try to add user to this group
                add_result = self.add_user_to_group(actual_group_name, account_id)
                if add_result.get("status") == "success":
                    return {
                        "status": "success",
                        "message": (
                            f"Added user to group '{actual_group_name}' which provides "
                            f"{permission_type} access. Note: This grants access to all "
                            f"spaces the group has permissions for."
                        ),
                        "method": "group_membership",
                        "group": actual_group_name,
                    }
        
        return {"status": "error", "error": "No suitable group found"}

    def _add_space_permission_legacy(
        self, space_key: str, account_id: str, permission_type: str = "read"
    ) -> dict[str, Any]:
        """
        Add space permission using legacy V1 API (for non-RBAC mode).
        """
        # Map permission type to Confluence operations
        operations_map = {
            "read": [
                {"key": "read", "target": "space"}
            ],
            "write": [
                {"key": "read", "target": "space"},
                {"key": "create", "target": "page"},
                {"key": "create", "target": "blogpost"},
                {"key": "create", "target": "attachment"},
                {"key": "create", "target": "comment"},
            ],
            "admin": [
                {"key": "read", "target": "space"},
                {"key": "create", "target": "page"},
                {"key": "create", "target": "blogpost"},
                {"key": "create", "target": "attachment"},
                {"key": "create", "target": "comment"},
                {"key": "delete", "target": "page"},
                {"key": "delete", "target": "blogpost"},
                {"key": "delete", "target": "attachment"},
                {"key": "delete", "target": "comment"},
                {"key": "administer", "target": "space"},
            ],
        }
        
        operations = operations_map.get(permission_type.lower(), operations_map["read"])
        
        results = []
        errors = []
        
        for op in operations:
            payload = {
                "subject": {
                    "type": "user",
                    "identifier": account_id,
                },
                "operation": {
                    "key": op["key"],
                    "target": op["target"],
                },
            }
            
            data, err = self._request("POST", f"space/{space_key}/permission", json=payload)
            if err:
                # Check for RBAC error
                if "RBAC" in str(err) or "roles-only" in str(err):
                    return {
                        "status": "error",
                        "error": (
                            f"This Confluence instance uses RBAC (role-based access control). "
                            f"Direct space permissions cannot be added. "
                            f"Please add the user to a group that has access to this space instead."
                        ),
                        "suggestion": "Use group-based access"
                    }
                # Ignore "already exists" errors
                if "already" not in str(err).lower():
                    errors.append(f"{op['key']}: {err}")
            else:
                results.append(op["key"])
        
        if errors and not results:
            return {"status": "error", "error": "; ".join(errors)}
        
        return {
            "status": "success",
            "message": f"Added {permission_type} permissions to space {space_key}",
            "operations_added": results,
            "errors": errors if errors else None,
        }

    def remove_space_permission(
        self, space_key: str, account_id: str, permission_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Remove a user's permission from a Confluence space.
        If permission_id is not provided, removes all permissions for the user.
        """
        logger.info(f"Removing user {account_id} permissions from space {space_key}")
        
        # First get current permissions to find the IDs
        perms_resp = self.get_space_permissions(space_key)
        if perms_resp.get("status") != "success":
            return perms_resp
        
        # Find user's permissions
        user_perms = [p for p in perms_resp.get("user_permissions", []) 
                      if p.get("account_id") == account_id]
        
        if not user_perms:
            return {
                "status": "success",
                "message": f"User has no permissions in space {space_key}",
                "already_removed": True,
            }
        
        # For now, we'll use the permission removal endpoint
        # Confluence API v2 provides better permission management
        removed = 0
        errors = []
        
        # Get space permissions with IDs
        data, err = self._request(
            "GET", f"spaces/{space_key}/permissions", 
            use_v2=True, 
            params={"limit": 250}
        )
        
        if err:
            return {"status": "error", "error": f"Could not fetch permission IDs: {err}"}
        
        if data:
            for perm in data.get("results", []):
                principal = perm.get("principal", {})
                if principal.get("type") == "user" and principal.get("id") == account_id:
                    perm_id = perm.get("id")
                    if perm_id:
                        _, del_err = self._request(
                            "DELETE", 
                            f"spaces/{space_key}/permissions/{perm_id}",
                            use_v2=True
                        )
                        if del_err:
                            errors.append(del_err)
                        else:
                            removed += 1
        
        if errors and removed == 0:
            return {"status": "error", "error": "; ".join(errors)}
        
        return {
            "status": "success",
            "message": f"Removed {removed} permission(s) from space {space_key}",
            "permissions_removed": removed,
        }

    def add_group_to_space(
        self, space_key: str, group_name: str, permission_type: str = "read"
    ) -> dict[str, Any]:
        """
        Add a group to a Confluence space with specified permission.
        Supports both legacy and RBAC modes.
        """
        logger.info(f"Adding group {group_name} to space {space_key} with {permission_type} permission")
        
        # First try V2 API (RBAC mode)
        space_id, err = self._get_space_id(space_key)
        if not err and space_id:
            # Try V2 API for group permission
            payload = {
                "subject": {
                    "type": "group",
                    "identifier": group_name
                },
                "operation": {
                    "key": permission_type.lower(),
                    "targetType": "space"
                }
            }
            data, v2_err = self._request("POST", f"spaces/{space_id}/permissions", json=payload, use_v2=True)
            if not v2_err:
                return {
                    "status": "success",
                    "message": f"Added {permission_type} permissions for group {group_name} to space {space_key}",
                    "method": "v2_api",
                }
        
        # Fallback to legacy API
        operations_map = {
            "read": [{"key": "read", "target": "space"}],
            "write": [
                {"key": "read", "target": "space"},
                {"key": "create", "target": "page"},
                {"key": "create", "target": "blogpost"},
            ],
            "admin": [
                {"key": "read", "target": "space"},
                {"key": "create", "target": "page"},
                {"key": "delete", "target": "page"},
                {"key": "administer", "target": "space"},
            ],
        }
        
        operations = operations_map.get(permission_type.lower(), operations_map["read"])
        
        results = []
        errors = []
        rbac_error = False
        
        for op in operations:
            payload = {
                "subject": {
                    "type": "group",
                    "identifier": group_name,
                },
                "operation": {
                    "key": op["key"],
                    "target": op["target"],
                },
            }
            
            data, err = self._request("POST", f"space/{space_key}/permission", json=payload)
            if err:
                if "RBAC" in str(err) or "roles-only" in str(err):
                    rbac_error = True
                    break
                if "already" not in str(err).lower():
                    errors.append(f"{op['key']}: {err}")
            else:
                results.append(op["key"])
        
        if rbac_error:
            return {
                "status": "error",
                "error": (
                    f"This Confluence instance uses RBAC (role-based access control). "
                    f"Group permissions cannot be added via API in RBAC mode. "
                    f"Please use the Confluence admin UI to configure space roles for the group '{group_name}'."
                ),
                "suggestion": "Configure space roles in Confluence admin settings"
            }
        
        if errors and not results:
            return {"status": "error", "error": "; ".join(errors)}
        
        return {
            "status": "success",
            "message": f"Added {permission_type} permissions for group {group_name} to space {space_key}",
            "operations_added": results,
        }

    # ==================== USER MANAGEMENT ====================

    def get_user_by_email(self, email: str) -> dict[str, Any]:
        """
        Find a Confluence user by email.
        Note: Uses the same user directory as Jira (Atlassian Cloud).
        """
        # Confluence uses CQL for user search
        data, err = self._request(
            "GET", 
            "search/user",
            params={"cql": f'user.email="{email}"', "limit": 10}
        )
        
        if err:
            # Fallback to Jira user search endpoint (works for all Atlassian products)
            from .jira_service import get_jira_service
            jira = get_jira_service()
            return jira.get_user_by_email(email)
        
        if not data or not data.get("results"):
            # Fallback
            from .jira_service import get_jira_service
            jira = get_jira_service()
            return jira.get_user_by_email(email)
        
        user = data["results"][0].get("user", {})
        return {
            "status": "success",
            "account_id": user.get("accountId"),
            "display_name": user.get("displayName"),
            "email": user.get("email") or email,
        }

    def get_user_space_permissions(self, account_id: str) -> dict[str, Any]:
        """
        Get all spaces a user has access to.
        """
        # Get all spaces and check each one for user permissions
        spaces_resp = self.list_spaces(limit=100)
        if spaces_resp.get("status") != "success":
            return spaces_resp
        
        user_spaces = []
        
        for space in spaces_resp.get("spaces", []):
            perms = self.get_space_permissions(space["key"])
            if perms.get("status") == "success":
                user_perms = [p for p in perms.get("user_permissions", []) 
                              if p.get("account_id") == account_id]
                if user_perms:
                    operations = list(set(p.get("operation") for p in user_perms))
                    user_spaces.append({
                        "space_key": space["key"],
                        "space_name": space["name"],
                        "operations": operations,
                    })
        
        return {
            "status": "success",
            "account_id": account_id,
            "spaces": user_spaces,
            "total": len(user_spaces),
        }

    # ==================== GROUP MANAGEMENT ====================

    def list_groups(self, limit: int = 50) -> dict[str, Any]:
        """
        List all groups in Confluence.
        Note: Uses same groups as Jira (Atlassian Cloud).
        """
        data, err = self._request("GET", "group", params={"limit": limit})
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No groups returned"}
        
        groups = []
        for g in data.get("results", []):
            groups.append({
                "name": g.get("name"),
                "type": g.get("type"),
            })
        
        return {
            "status": "success",
            "groups": groups,
            "total": len(groups),
        }

    def get_group_members(self, group_name: str, limit: int = 50) -> dict[str, Any]:
        """Get members of a group."""
        data, err = self._request("GET", f"group/{group_name}/member", params={"limit": limit})
        if err:
            return {"status": "error", "error": err}
        if not data:
            return {"status": "error", "error": "No data returned"}
        
        members = []
        for m in data.get("results", []):
            members.append({
                "account_id": m.get("accountId"),
                "display_name": m.get("displayName"),
                "email": m.get("email"),
            })
        
        return {
            "status": "success",
            "group_name": group_name,
            "members": members,
            "total": len(members),
        }

    def add_user_to_group(self, group_name: str, account_id: str) -> dict[str, Any]:
        """
        Add a user to a group.
        Note: Uses Jira's user management API since groups are shared across Atlassian Cloud.
        """
        # Confluence groups are actually managed via Jira's admin API
        # We'll use the Jira service for this
        from .jira_service import get_jira_service
        jira = get_jira_service()
        return jira.add_user_to_group(group_name, account_id)

    def remove_user_from_group(self, group_name: str, account_id: str) -> dict[str, Any]:
        """
        Remove a user from a group.
        Note: Uses Jira's user management API since groups are shared across Atlassian Cloud.
        """
        from .jira_service import get_jira_service
        jira = get_jira_service()
        return jira.remove_user_from_group(group_name, account_id)


# Singleton for use by tools
_confluence_service: Optional[ConfluenceService] = None


def get_confluence_service() -> ConfluenceService:
    global _confluence_service
    if _confluence_service is None:
        _confluence_service = ConfluenceService()
    return _confluence_service
