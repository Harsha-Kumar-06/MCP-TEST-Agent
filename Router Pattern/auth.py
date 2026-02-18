"""
Authentication module for CorpAssist.
Supports multiple authentication methods for enterprise deployment.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from functools import wraps
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# User Models
# =============================================================================

class User(BaseModel):
    """Authenticated user model with organization context."""
    employee_id: str
    email: str
    full_name: str
    department: str
    role: str  # employee, manager, admin
    manager_email: Optional[str] = None
    location: Optional[str] = None
    
    
class AuthToken(BaseModel):
    """Authentication token."""
    token: str
    user: User
    expires_at: datetime
    

# =============================================================================
# Mock User Directory (Replace with real LDAP/AD in production)
# =============================================================================

MOCK_USERS = {
    "john.doe@company.com": {
        "employee_id": "EMP001",
        "email": "john.doe@company.com",
        "full_name": "John Doe",
        "department": "Engineering",
        "role": "employee",
        "manager_email": "jane.smith@company.com",
        "location": "San Francisco",
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
    },
    "jane.smith@company.com": {
        "employee_id": "EMP002",
        "email": "jane.smith@company.com",
        "full_name": "Jane Smith",
        "department": "Engineering",
        "role": "manager",
        "manager_email": "cto@company.com",
        "location": "San Francisco",
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
    },
    "admin@company.com": {
        "employee_id": "EMP000",
        "email": "admin@company.com",
        "full_name": "System Admin",
        "department": "IT",
        "role": "admin",
        "manager_email": None,
        "location": "Headquarters",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
    },
}

# In-memory token store (use Redis in production)
ACTIVE_TOKENS: dict[str, AuthToken] = {}


# =============================================================================
# Authentication Providers
# =============================================================================

class AuthProvider:
    """Base authentication provider."""
    
    def authenticate(self, credentials: dict) -> Optional[User]:
        raise NotImplementedError
        
    def validate_token(self, token: str) -> Optional[User]:
        raise NotImplementedError


class BasicAuthProvider(AuthProvider):
    """
    Basic email/password authentication.
    Good for development and small deployments.
    """
    
    def authenticate(self, credentials: dict) -> Optional[User]:
        email = credentials.get("email", "").lower()
        password = credentials.get("password", "")
        
        if email not in MOCK_USERS:
            return None
            
        user_data = MOCK_USERS[email]
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if password_hash != user_data["password_hash"]:
            return None
            
        return User(
            employee_id=user_data["employee_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            department=user_data["department"],
            role=user_data["role"],
            manager_email=user_data.get("manager_email"),
            location=user_data.get("location"),
        )
    
    def create_token(self, user: User, expires_hours: int = 8) -> AuthToken:
        """Create a session token for authenticated user."""
        token = secrets.token_urlsafe(32)
        auth_token = AuthToken(
            token=token,
            user=user,
            expires_at=datetime.now() + timedelta(hours=expires_hours),
        )
        ACTIVE_TOKENS[token] = auth_token
        return auth_token
    
    def validate_token(self, token: str) -> Optional[User]:
        """Validate a token and return the user if valid."""
        if token not in ACTIVE_TOKENS:
            return None
            
        auth_token = ACTIVE_TOKENS[token]
        
        if datetime.now() > auth_token.expires_at:
            del ACTIVE_TOKENS[token]
            return None
            
        return auth_token.user
    
    def revoke_token(self, token: str) -> bool:
        """Revoke/logout a token."""
        if token in ACTIVE_TOKENS:
            del ACTIVE_TOKENS[token]
            return True
        return False


class SSOAuthProvider(AuthProvider):
    """
    SSO/SAML authentication provider.
    Integrates with enterprise identity providers like:
    - Okta
    - Azure AD
    - Google Workspace
    - OneLogin
    
    In production, this would validate SAML assertions.
    """
    
    def __init__(self):
        self.sso_enabled = os.getenv("SSO_ENABLED", "false").lower() == "true"
        self.sso_provider = os.getenv("SSO_PROVIDER", "okta")
        self.sso_issuer = os.getenv("SSO_ISSUER_URL", "")
        self.sso_client_id = os.getenv("SSO_CLIENT_ID", "")
        
    def authenticate(self, credentials: dict) -> Optional[User]:
        """
        Validate SSO token/assertion.
        In production, this would:
        1. Validate SAML assertion signature
        2. Check assertion is from trusted IdP
        3. Extract user attributes from assertion
        4. Map to internal User model
        """
        sso_token = credentials.get("sso_token")
        
        if not sso_token:
            return None
            
        # In production: Validate with IdP
        # For demo: Accept any token and return mock user
        return User(
            employee_id="SSO001",
            email="sso.user@company.com",
            full_name="SSO User",
            department="Unknown",
            role="employee",
        )
    
    def get_login_url(self, redirect_uri: str) -> str:
        """Get SSO login URL for redirect."""
        # In production: Generate SAML AuthnRequest or OAuth URL
        return f"{self.sso_issuer}/authorize?client_id={self.sso_client_id}&redirect_uri={redirect_uri}"
    
    def validate_token(self, token: str) -> Optional[User]:
        return None  # SSO tokens validated via authenticate()


class LDAPAuthProvider(AuthProvider):
    """
    LDAP/Active Directory authentication.
    Integrates with corporate directory services.
    
    In production, this would connect to LDAP server.
    """
    
    def __init__(self):
        self.ldap_server = os.getenv("LDAP_SERVER", "ldap://localhost:389")
        self.ldap_base_dn = os.getenv("LDAP_BASE_DN", "dc=company,dc=com")
        self.ldap_bind_dn = os.getenv("LDAP_BIND_DN", "")
        self.ldap_bind_password = os.getenv("LDAP_BIND_PASSWORD", "")
        
    def authenticate(self, credentials: dict) -> Optional[User]:
        """
        Authenticate against LDAP/AD.
        In production, this would:
        1. Connect to LDAP server
        2. Bind with service account
        3. Search for user by email/username
        4. Attempt bind with user credentials
        5. Fetch user attributes (department, manager, etc.)
        """
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        
        if not username or not password:
            return None
            
        # In production: Use python-ldap to authenticate
        # import ldap
        # conn = ldap.initialize(self.ldap_server)
        # conn.simple_bind_s(f"cn={username},{self.ldap_base_dn}", password)
        
        # For demo: Use mock users
        email = username if "@" in username else f"{username}@company.com"
        return BasicAuthProvider().authenticate({
            "email": email,
            "password": password,
        })
    
    def validate_token(self, token: str) -> Optional[User]:
        return BasicAuthProvider().validate_token(token)


class OAuthProvider(AuthProvider):
    """
    OAuth 2.0 provider for Google Workspace, Microsoft 365, etc.
    """
    
    def __init__(self, provider: str = "google"):
        self.provider = provider
        self.client_id = os.getenv(f"{provider.upper()}_CLIENT_ID", "")
        self.client_secret = os.getenv(f"{provider.upper()}_CLIENT_SECRET", "")
        self.redirect_uri = os.getenv(f"{provider.upper()}_REDIRECT_URI", "")
        
        self.provider_config = {
            "google": {
                "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v3/userinfo",
                "scopes": ["openid", "email", "profile"],
            },
            "microsoft": {
                "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me",
                "scopes": ["openid", "email", "profile", "User.Read"],
            },
        }
    
    def get_auth_url(self, state: str) -> str:
        """Generate OAuth authorization URL."""
        config = self.provider_config.get(self.provider, {})
        scopes = "+".join(config.get("scopes", []))
        
        return (
            f"{config['auth_url']}?"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type=code&"
            f"scope={scopes}&"
            f"state={state}"
        )
    
    def authenticate(self, credentials: dict) -> Optional[User]:
        """
        Exchange OAuth code for tokens and fetch user info.
        In production, this would make actual HTTP requests.
        """
        auth_code = credentials.get("code")
        
        if not auth_code:
            return None
            
        # In production:
        # 1. Exchange code for access token
        # 2. Fetch user info from provider
        # 3. Map to internal User model
        
        return None
    
    def validate_token(self, token: str) -> Optional[User]:
        return BasicAuthProvider().validate_token(token)


# =============================================================================
# Authentication Manager
# =============================================================================

class AuthManager:
    """
    Central authentication manager.
    Handles multiple auth providers based on configuration.
    """
    
    def __init__(self):
        self.auth_method = os.getenv("AUTH_METHOD", "basic").lower()
        
        self.providers = {
            "basic": BasicAuthProvider(),
            "ldap": LDAPAuthProvider(),
            "sso": SSOAuthProvider(),
            "oauth_google": OAuthProvider("google"),
            "oauth_microsoft": OAuthProvider("microsoft"),
        }
        
    def get_provider(self) -> AuthProvider:
        """Get the configured auth provider."""
        return self.providers.get(self.auth_method, BasicAuthProvider())
    
    def authenticate(self, credentials: dict) -> Optional[AuthToken]:
        """Authenticate user and return token."""
        provider = self.get_provider()
        user = provider.authenticate(credentials)
        
        if not user:
            return None
            
        # Always use BasicAuthProvider for token management
        return BasicAuthProvider().create_token(user)
    
    def validate_token(self, token: str) -> Optional[User]:
        """Validate token and return user."""
        return BasicAuthProvider().validate_token(token)
    
    def logout(self, token: str) -> bool:
        """Logout/revoke token."""
        return BasicAuthProvider().revoke_token(token)


# =============================================================================
# Audit Logger
# =============================================================================

class AuditLogger:
    """
    Audit logger for compliance tracking.
    Logs all user interactions with the agent.
    """
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        
    def log(
        self,
        user: User,
        action: str,
        details: dict,
        ip_address: str = None,
    ):
        """Log an audit event."""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "employee_id": user.employee_id,
            "email": user.email,
            "department": user.department,
            "action": action,
            "details": details,
            "ip_address": ip_address,
        }
        
        # In production: Send to SIEM, Splunk, CloudWatch, etc.
        with open(self.log_file, "a") as f:
            f.write(f"{log_entry}\n")
            
        return log_entry
    
    def log_chat(self, user: User, message: str, response: str, ip: str = None):
        """Log a chat interaction."""
        return self.log(
            user=user,
            action="chat_message",
            details={
                "message": message[:500],  # Truncate for logs
                "response": response[:500],
            },
            ip_address=ip,
        )
    
    def log_escalation(self, user: User, reason: str, target: str, ip: str = None):
        """Log an escalation request."""
        return self.log(
            user=user,
            action="escalation_requested",
            details={
                "reason": reason,
                "escalated_to": target,
            },
            ip_address=ip,
        )
    
    def log_tool_use(self, user: User, tool: str, params: dict, ip: str = None):
        """Log tool usage."""
        return self.log(
            user=user,
            action="tool_invoked",
            details={
                "tool": tool,
                "parameters": params,
            },
            ip_address=ip,
        )


# Global instances
auth_manager = AuthManager()
audit_logger = AuditLogger()
