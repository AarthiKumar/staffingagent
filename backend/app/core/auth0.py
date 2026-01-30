"""
Auth0 authentication and role-based access control.

Supports three user roles:
- superuser: Can manage users, full system access
- project_manager: Can search for staff, update availability
- staff: Can upload and update their own CVs
"""
from enum import Enum
from typing import Optional, List
from functools import wraps

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

security = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """User roles in the system"""
    SUPERUSER = "superuser"
    PROJECT_MANAGER = "project_manager"
    STAFF = "staff"


class User:
    """Authenticated user model"""

    def __init__(self, sub: str, email: str, roles: List[str], name: Optional[str] = None):
        self.sub = sub  # Auth0 user ID
        self.email = email
        self.name = name or email
        self.roles = roles

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role"""
        return role.value in self.roles

    def has_any_role(self, *roles: UserRole) -> bool:
        """Check if user has any of the specified roles"""
        return any(role.value in self.roles for role in roles)

    @property
    def is_superuser(self) -> bool:
        return self.has_role(UserRole.SUPERUSER)

    @property
    def is_project_manager(self) -> bool:
        return self.has_role(UserRole.PROJECT_MANAGER)

    @property
    def is_staff(self) -> bool:
        return self.has_role(UserRole.STAFF)


class Auth0TokenValidator:
    """Validates Auth0 JWT tokens"""

    def __init__(self):
        self.domain = settings.auth0_domain
        self.audience = settings.auth0_audience
        self.enabled = settings.auth0_enabled

        if self.enabled and self.domain:
            # Initialize JWK client for fetching Auth0 public keys
            self.jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            self.jwks_client = PyJWKClient(self.jwks_url)
            logger.info(f"Auth0 validation enabled for domain: {self.domain}")
        else:
            self.jwks_client = None
            logger.info("Auth0 validation disabled")

    def verify_token(self, token: str) -> dict:
        """
        Verify and decode an Auth0 JWT token

        Args:
            token: The JWT token string

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid
        """
        if not self.enabled:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Authentication is not enabled"
            )

        try:
            # Get signing key from Auth0 JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate the token
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Global token validator instance
token_validator = Auth0TokenValidator()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from JWT token

    Dependency for endpoints that require authentication.

    Args:
        credentials: HTTP Bearer token from request

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify and decode token
    payload = token_validator.verify_token(credentials.credentials)

    # Extract user info from token
    sub = payload.get("sub")
    email = payload.get("email")
    name = payload.get("name")

    # Get roles from custom claim (namespace required by Auth0)
    # Roles should be added to the token via Auth0 Rule or Action
    roles_claim = payload.get("https://staffingagent.com/roles", [])
    if not isinstance(roles_claim, list):
        roles_claim = [roles_claim] if roles_claim else []

    if not sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    user = User(sub=sub, email=email, roles=roles_claim, name=name)
    logger.info(f"Authenticated user: {user.email} with roles: {user.roles}")

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[User]:
    """
    Get current user if authenticated, else None

    Use this for endpoints that work with or without authentication.
    """
    if not credentials or not settings.auth0_enabled:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_roles(*required_roles: UserRole):
    """
    Decorator to enforce role-based access control on endpoints

    Usage:
        @router.get("/admin")
        @require_roles(UserRole.SUPERUSER)
        async def admin_endpoint(user: User = Depends(get_current_user)):
            ...

    Args:
        *required_roles: One or more UserRole values required to access the endpoint

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: User = Depends(get_current_user), **kwargs):
            # Check if user has any of the required roles
            if not user.has_any_role(*required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {[r.value for r in required_roles]}"
                )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator


# Role-specific dependencies for convenience
async def require_superuser(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires superuser role"""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return user


async def require_project_manager(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires project_manager or superuser role"""
    if not (user.is_project_manager or user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project Manager access required"
        )
    return user


async def require_staff(user: User = Depends(get_current_user)) -> User:
    """Dependency that requires staff role (or higher)"""
    if not (user.is_staff or user.is_project_manager or user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return user
