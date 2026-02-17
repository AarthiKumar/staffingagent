"""Auth0 JWT validation and role-based access control"""
from typing import List, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from .config import settings

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# Namespace for custom Auth0 claims (set via Auth0 Action)
CLAIMS_NAMESPACE = "https://staffingagent/"

# Permission constants
PERM_MANAGE_USERS = "manage:users"
PERM_MANAGE_CVS = "manage:cvs"
PERM_MANAGE_AVAILABILITY = "manage:availability"
PERM_SEARCH_CANDIDATES = "search:candidates"
PERM_VIEW_CANDIDATES = "view:candidates"
PERM_UPLOAD_CV = "upload:cv"
PERM_EDIT_OWN_CV = "edit:own_cv"
PERM_EDIT_OWN_AVAILABILITY = "edit:own_availability"

# Role constants
ROLE_SUPERUSER = "superuser"
ROLE_PROJECT_MANAGER = "project_manager"
ROLE_CANDIDATE = "candidate"

_jwks_cache: Optional[dict] = None


def _get_jwks() -> dict:
    """Fetch Auth0 JWKS for token validation (cached in memory)"""
    global _jwks_cache
    if _jwks_cache is None:
        if not settings.auth0_domain:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Auth0 not configured. Set AUTH0_DOMAIN in .env",
            )
        url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache


def verify_token(token: str) -> dict:
    """Validate Auth0 JWT and return claims"""
    if not settings.auth0_domain or not settings.auth0_audience:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auth0 not configured. Set AUTH0_DOMAIN and AUTH0_AUDIENCE in .env",
        )
    jwks = _get_jwks()
    try:
        # Decode without verification first to inspect claims for debugging
        import logging
        _logger = logging.getLogger(__name__)
        unverified = jwt.get_unverified_claims(token)
        _logger.warning(f"[AUTH DEBUG] Token aud claim: {unverified.get('aud')}")
        _logger.warning(f"[AUTH DEBUG] Backend AUTH0_AUDIENCE: {settings.auth0_audience!r}")
        _logger.warning(f"[AUTH DEBUG] Token iss claim: {unverified.get('iss')}")
        _logger.warning(f"[AUTH DEBUG] Expected issuer: https://{settings.auth0_domain}/")

        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=f"https://{settings.auth0_domain}/",
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user from Auth0 token"""
    payload = verify_token(credentials.credentials)
    return {
        "sub": payload.get("sub"),
        "email": payload.get(f"{CLAIMS_NAMESPACE}email") or payload.get("email"),
        "roles": payload.get(f"{CLAIMS_NAMESPACE}roles", []),
        "permissions": payload.get("permissions", []),
    }


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
) -> Optional[dict]:
    """Get current user if authenticated, else None"""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_permission(*permissions: str):
    """Dependency factory: require at least one of the listed permissions"""

    async def check(user: dict = Depends(get_current_user)) -> dict:
        user_perms = set(user.get("permissions", []))
        if not any(p in user_perms for p in permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission. Required one of: {list(permissions)}",
            )
        return user

    return check


def require_role(*roles: str):
    """Dependency factory: require at least one of the listed roles"""

    async def check(user: dict = Depends(get_current_user)) -> dict:
        user_roles = set(user.get("roles", []))
        if not any(r in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role. Required one of: {list(roles)}",
            )
        return user

    return check


# Convenience dependencies
RequireSuperuser = require_role(ROLE_SUPERUSER)
RequireManagerOrAbove = require_role(ROLE_SUPERUSER, ROLE_PROJECT_MANAGER)
RequireAnyRole = require_role(ROLE_SUPERUSER, ROLE_PROJECT_MANAGER, ROLE_CANDIDATE)
