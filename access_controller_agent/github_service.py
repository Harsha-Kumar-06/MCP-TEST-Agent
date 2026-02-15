"""
GitHub Cloud REST API service for access management.
Supports: organization membership, repository collaborators, and teams.

Authentication model:
- GitHub App JWT -> Installation access token
- Installation token cached in-memory until close to expiry

Required Environment Variables:
- GITHUB_ORG
- GITHUB_APP_ID
- GITHUB_APP_PRIVATE_KEY

Optional Environment Variables:
- GITHUB_INSTALLATION_ID (auto-discovered from org when missing)
- GITHUB_API_BASE_URL (default: https://api.github.com)
- GITHUB_API_VERSION (default: 2022-11-28)
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

try:
    import jwt
except ImportError:  # pragma: no cover
    jwt = None

import requests

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self) -> None:
        self.org = os.getenv("GITHUB_ORG", "").strip()
        self.app_id = os.getenv("GITHUB_APP_ID", "").strip()
        self.installation_id = os.getenv("GITHUB_INSTALLATION_ID", "").strip()
        self.api_base_url = os.getenv("GITHUB_API_BASE_URL", "https://api.github.com").rstrip("/")
        self.api_version = os.getenv("GITHUB_API_VERSION", "2022-11-28")
        self.private_key = self._load_private_key(os.getenv("GITHUB_APP_PRIVATE_KEY", ""))
        self._is_user_account = os.getenv("GITHUB_USE_USER_ACCOUNT", "").strip().lower() in ("1", "true", "yes")

        self._token: Optional[str] = None
        self._token_expires_at: float = 0
        self._is_user_account: bool = False  # True when app is installed on user account, not org

        self._session = requests.Session()

    def is_configured(self) -> bool:
        return bool(self.org and self.app_id and self.private_key and jwt is not None)

    def _org_only_error(self, operation: str) -> dict[str, Any]:
        """Return a clear error when an org-only operation is used with a personal account."""
        return {
            "status": "error",
            "error": f"'{operation}' is only available for GitHub organizations. Personal accounts do not have organization members, invitations, or teams. Use repository-level actions (e.g. grant/revoke repo access) instead.",
            "user_account": True,
        }

    @staticmethod
    def _load_private_key(raw: str) -> str:
        """Load private key from env: inline PEM content or path to a .pem file."""
        raw = (raw or "").strip()
        if not raw:
            return ""
        # Inline PEM: starts with -----BEGIN
        if "-----BEGIN" in raw:
            return raw.replace("\\n", "\n").strip()
        # Treat as file path (absolute or relative to cwd / package dir)
        path = Path(raw)
        if not path.is_absolute():
            # Try cwd first, then directory of this file (access_controller_agent)
            for base in (Path.cwd(), Path(__file__).resolve().parent):
                candidate = base / path
                if candidate.is_file():
                    path = candidate
                    break
            else:
                path = Path.cwd() / path
        if path.is_file():
            try:
                return path.read_text(encoding="utf-8").strip()
            except Exception as e:
                logger.warning("Could not read GitHub private key file %s: %s", path, e)
                return ""
        logger.warning("GitHub private key path not found: %s", raw)
        return ""

    def _parse_repo(self, repo: str) -> tuple[str, str]:
        """Return (owner, repo_name). If repo is 'owner/name', split; else owner is org."""
        repo = (repo or "").strip()
        if "/" in repo:
            owner, repo_name = repo.split("/", 1)
            return owner.strip(), repo_name.strip()
        return self.org, repo

    def _build_app_jwt(self) -> str:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 540, "iss": self.app_id}
        if jwt is None:
            raise RuntimeError("PyJWT is required for GitHub App authentication")
        token = jwt.encode(payload, self.private_key, algorithm="RS256")
        return token if isinstance(token, str) else token.decode("utf-8")

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
        auth_mode: str = "installation",
    ) -> tuple[Optional[Any], Optional[dict[str, Any]]]:
        if not self.is_configured():
            return None, {"status": "error", "error": "GitHub App is not configured."}

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.api_version,
        }

        if auth_mode == "app":
            headers["Authorization"] = f"Bearer {self._build_app_jwt()}"
        else:
            token = self._get_installation_token()
            if not token:
                return None, {"status": "error", "error": "Could not obtain GitHub installation token."}
            headers["Authorization"] = f"Bearer {token}"

        url = f"{self.api_base_url}/{path.lstrip('/')}"

        try:
            resp = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=headers,
                timeout=30,
            )

            if resp.status_code in (403, 429):
                return None, {
                    "status": "error",
                    "error": "GitHub API rate limit or permission issue.",
                    "code": resp.status_code,
                    "retry_after": resp.headers.get("Retry-After"),
                    "details": self._extract_error_message(resp),
                }

            if resp.status_code in (404, 422):
                return None, {
                    "status": "error",
                    "error": self._extract_error_message(resp),
                    "code": resp.status_code,
                }

            if resp.status_code >= 400:
                return None, {
                    "status": "error",
                    "error": self._extract_error_message(resp),
                    "code": resp.status_code,
                }

            if not resp.text:
                return {}, None
            return resp.json(), None

        except requests.RequestException as exc:
            return None, {"status": "error", "error": str(exc)}

    @staticmethod
    def _extract_error_message(resp: requests.Response) -> str:
        try:
            payload = resp.json()
            if isinstance(payload, dict):
                if payload.get("message"):
                    return payload["message"]
                if payload.get("error"):
                    return payload["error"]
            return f"GitHub API error ({resp.status_code})"
        except Exception:
            return f"GitHub API error ({resp.status_code})"

    def _get_installation_id(self) -> Optional[str]:
        if self.installation_id:
            return self.installation_id

        # Try organization first, then user account (personal)
        data, err = self._request("GET", f"orgs/{self.org}/installation", auth_mode="app")
        if err and err.get("code") == 404:
            data, err = self._request("GET", f"users/{self.org}/installation", auth_mode="app")
            if not err and isinstance(data, dict):
                self._is_user_account = True  # detected: app installed on user account
        if err:
            logger.error("Failed to resolve installation id: %s", err)
            return None

        installation_id = data.get("id") if isinstance(data, dict) else None
        if installation_id:
            self.installation_id = str(installation_id)
            return self.installation_id
        return None

    def _get_installation_token(self) -> Optional[str]:
        if self._token and time.time() < (self._token_expires_at - 120):
            return self._token

        installation_id = self._get_installation_id()
        if not installation_id:
            return None

        data, err = self._request(
            "POST",
            f"app/installations/{installation_id}/access_tokens",
            auth_mode="app",
        )
        if err:
            logger.error("Failed to create installation token: %s", err)
            return None

        token = data.get("token")
        expires_at = data.get("expires_at")
        if not token or not expires_at:
            return None

        parsed = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        self._token = token
        self._token_expires_at = parsed.timestamp()
        return token

    def resolve_user_identifier(self, user_identifier: str) -> dict[str, Any]:
        user_identifier = (user_identifier or "").strip()
        if not user_identifier:
            return {"status": "error", "error": "User identifier is required."}

        if "@" not in user_identifier:
            return {"status": "success", "username": user_identifier, "source": "username"}

        # Personal account: no org invitations or members list to resolve email → username
        if self._is_user_account:
            return {
                "status": "error",
                "needs_username": True,
                "email": user_identifier.lower(),
                "error": "Could not resolve GitHub username from email. Ask user for their GitHub username.",
            }

        email = user_identifier.lower()

        invites = self.list_org_invitations()
        if invites.get("status") == "success":
            for inv in invites.get("invitations", []):
                if (inv.get("email") or "").lower() == email:
                    return {
                        "status": "partial",
                        "pending_invitation": True,
                        "email": email,
                        "message": f"{email} already has a pending GitHub organization invitation.",
                    }

        candidate = email.split("@", 1)[0]
        member_check = self.is_org_member(candidate)
        if member_check.get("status") == "success" and member_check.get("is_member"):
            return {
                "status": "success",
                "username": candidate,
                "email": email,
                "source": "email_local_part",
            }

        return {
            "status": "error",
            "needs_username": True,
            "email": email,
            "error": "Could not resolve GitHub username from email. Ask user for GitHub username.",
        }

    def is_org_member(self, username: str) -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("Organization membership check")
        _, err = self._request("GET", f"orgs/{self.org}/members/{username}")
        if not err:
            return {"status": "success", "is_member": True}
        if err.get("code") == 404:
            return {"status": "success", "is_member": False}
        return err

    def invite_user_to_org(self, user_email: str, role: str = "member") -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("Invite to organization")
        data, err = self._request(
            "POST",
            f"orgs/{self.org}/invitations",
            json={"email": user_email, "role": role},
        )
        if err:
            return err
        return {
            "status": "success",
            "message": f"Invited {user_email} to GitHub organization '{self.org}' as {role}.",
            "invitation": data,
        }

    def remove_user_from_org(self, username: str) -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("Remove from organization")
        _, err = self._request("DELETE", f"orgs/{self.org}/members/{username}")
        if not err:
            return {"status": "success", "message": f"Removed '{username}' from organization '{self.org}'."}
        if err.get("code") == 404:
            _, outside_err = self._request("DELETE", f"orgs/{self.org}/outside_collaborators/{username}")
            if not outside_err:
                return {
                    "status": "success",
                    "message": f"Removed outside collaborator '{username}' from '{self.org}'.",
                }
        return err

    def list_org_members(self, membership_filter: str = "all") -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("List organization members")
        data, err = self._request(
            "GET", f"orgs/{self.org}/members", params={"filter": membership_filter, "per_page": 100}
        )
        if err:
            return err
        members = [{"login": i.get("login"), "id": i.get("id"), "type": i.get("type")} for i in (data or [])]
        return {"status": "success", "members": members, "total": len(members)}

    def list_org_invitations(self) -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("List organization invitations")
        data, err = self._request("GET", f"orgs/{self.org}/invitations", params={"per_page": 100})
        if err:
            return err
        invitations = [
            {
                "id": i.get("id"),
                "email": i.get("email"),
                "role": i.get("role"),
                "created_at": i.get("created_at"),
            }
            for i in (data or [])
        ]
        return {"status": "success", "invitations": invitations, "total": len(invitations)}

    def list_org_repositories(self, limit: int = 100) -> dict[str, Any]:
        # Use installation/repositories so it works for both org and user account
        if not self._get_installation_token():
            return {"status": "error", "error": "Could not obtain installation token."}
        data, err = self._request(
            "GET", "installation/repositories", params={"per_page": min(limit, 100)}
        )
        if err:
            return err
        repos_list = (data or {}).get("repositories", []) if isinstance(data, dict) else (data or [])
        repos = [
            {
                "name": i.get("name"),
                "full_name": i.get("full_name"),
                "private": i.get("private", True),
            }
            for i in repos_list
        ]
        return {"status": "success", "repositories": repos, "total": len(repos)}

    def grant_repository_access(self, username: str, repo: str, permission: str = "push") -> dict[str, Any]:
        owner, repo_name = self._parse_repo(repo)
        data, err = self._request(
            "PUT", f"repos/{owner}/{repo_name}/collaborators/{username}", json={"permission": permission}
        )
        if err:
            return err
        return {
            "status": "success",
            "message": f"Granted {permission} access to '{username}' on '{owner}/{repo_name}'.",
            "result": data,
        }

    def revoke_repository_access(self, username: str, repo: str) -> dict[str, Any]:
        owner, repo_name = self._parse_repo(repo)
        _, err = self._request("DELETE", f"repos/{owner}/{repo_name}/collaborators/{username}")
        if err:
            return err
        return {
            "status": "success",
            "message": f"Revoked repository access for '{username}' on '{owner}/{repo_name}'.",
        }

    def get_repository_user_permission(self, username: str, repo: str) -> dict[str, Any]:
        owner, repo_name = self._parse_repo(repo)
        data, err = self._request("GET", f"repos/{owner}/{repo_name}/collaborators/{username}/permission")
        if err:
            return err
        return {
            "status": "success",
            "repository": f"{owner}/{repo_name}",
            "username": username,
            "permission": data.get("permission"),
            "role_name": data.get("role_name"),
            "user": data.get("user", {}),
        }

    def list_repository_collaborators(self, repo: str, affiliation: str = "all") -> dict[str, Any]:
        owner, repo_name = self._parse_repo(repo)
        data, err = self._request(
            "GET",
            f"repos/{owner}/{repo_name}/collaborators",
            params={"affiliation": affiliation, "per_page": 100},
        )
        if err:
            return err
        collabs = [{"login": i.get("login"), "id": i.get("id"), "type": i.get("type")} for i in (data or [])]
        return {
            "status": "success",
            "repository": f"{owner}/{repo_name}",
            "collaborators": collabs,
            "total": len(collabs),
        }

    def list_teams(self) -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("List teams")
        data, err = self._request("GET", f"orgs/{self.org}/teams", params={"per_page": 100})
        if err:
            return err
        teams = [{"name": i.get("name"), "slug": i.get("slug"), "privacy": i.get("privacy")} for i in (data or [])]
        return {"status": "success", "teams": teams, "total": len(teams)}

    def add_user_to_team(self, username: str, team_slug: str, role: str = "member") -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("Add user to team")
        data, err = self._request(
            "PUT", f"orgs/{self.org}/teams/{team_slug}/memberships/{username}", json={"role": role}
        )
        if err:
            return err
        return {
            "status": "success",
            "message": f"Added '{username}' to team '{team_slug}' as {role}.",
            "result": data,
        }

    def remove_user_from_team(self, username: str, team_slug: str) -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("Remove user from team")
        _, err = self._request("DELETE", f"orgs/{self.org}/teams/{team_slug}/memberships/{username}")
        if err:
            return err
        return {"status": "success", "message": f"Removed '{username}' from team '{team_slug}'."}

    def grant_team_repo_access(self, team_slug: str, repo: str, permission: str = "push") -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("Grant team repository access")
        owner, repo_name = self._parse_repo(repo)
        _, err = self._request(
            "PUT", f"orgs/{self.org}/teams/{team_slug}/repos/{owner}/{repo_name}", json={"permission": permission}
        )
        if err:
            return err
        return {
            "status": "success",
            "message": f"Granted team '{team_slug}' {permission} access to '{owner}/{repo_name}'.",
        }

    def revoke_team_repo_access(self, team_slug: str, repo: str) -> dict[str, Any]:
        if self._is_user_account:
            return self._org_only_error("Revoke team repository access")
        owner, repo_name = self._parse_repo(repo)
        _, err = self._request("DELETE", f"orgs/{self.org}/teams/{team_slug}/repos/{owner}/{repo_name}")
        if err:
            return err
        return {
            "status": "success",
            "message": f"Revoked team '{team_slug}' access from '{owner}/{repo_name}'.",
        }


_github_service: Optional[GitHubService] = None


def get_github_service() -> GitHubService:
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service
