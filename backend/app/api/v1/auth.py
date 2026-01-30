"""Authentication endpoints"""
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
import httpx

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


# TODO: Load users from database
# Stub local auth with hardcoded user
STUB_USERS = {
    "admin": {
        "username": "admin",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYBn0VWZ6Yu",  # "admin"
    }
}


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    """Local authentication login"""
    user = STUB_USERS.get(req.username)

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(data={"sub": req.username, "username": req.username})

    return LoginResponse(access_token=access_token, token_type="bearer")


# ========== Auth0 Endpoints ==========


class AuthURLResponse(BaseModel):
    """Response containing Auth0 authorization URL"""
    auth_url: str


class TokenResponse(BaseModel):
    """OAuth token response"""
    access_token: str
    id_token: str
    token_type: str
    expires_in: int


@router.get("/auth0/login")
async def auth0_login(redirect_uri: Optional[str] = None):
    """
    Initiate Auth0 login flow

    Returns the Auth0 authorization URL that the frontend should redirect to.

    Query params:
        redirect_uri: Optional custom redirect URI after login
    """
    if not settings.auth0_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auth0 authentication is not enabled. Set AUTH0_ENABLED=true in .env"
        )

    callback_url = redirect_uri or settings.auth0_callback_url

    # Build Auth0 authorization URL
    params = {
        "response_type": "code",
        "client_id": settings.auth0_client_id,
        "redirect_uri": callback_url,
        "scope": "openid profile email",
        "audience": settings.auth0_audience,
    }

    auth_url = f"https://{settings.auth0_domain}/authorize?{urlencode(params)}"

    logger.info(f"Generated Auth0 login URL for callback: {callback_url}")

    return AuthURLResponse(auth_url=auth_url)


@router.get("/auth0/callback")
async def auth0_callback(
    code: str = Query(..., description="Authorization code from Auth0"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
):
    """
    Auth0 callback endpoint

    Exchanges the authorization code for access and ID tokens.

    Query params:
        code: Authorization code from Auth0
        state: Optional state parameter for CSRF protection
    """
    if not settings.auth0_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auth0 authentication is not enabled"
        )

    # Exchange code for tokens
    token_url = f"https://{settings.auth0_domain}/oauth/token"

    payload = {
        "grant_type": "authorization_code",
        "client_id": settings.auth0_client_id,
        "client_secret": settings.auth0_client_secret,
        "code": code,
        "redirect_uri": settings.auth0_callback_url,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, json=payload)

            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to exchange code for token: {response.text}"
                )

            tokens = response.json()

            logger.info("Successfully exchanged authorization code for tokens")

            return TokenResponse(
                access_token=tokens["access_token"],
                id_token=tokens["id_token"],
                token_type=tokens.get("token_type", "Bearer"),
                expires_in=tokens.get("expires_in", 3600),
            )

    except httpx.HTTPError as e:
        logger.error(f"HTTP error during token exchange: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to communicate with Auth0"
        )


@router.get("/auth0/logout")
async def auth0_logout(return_to: Optional[str] = None):
    """
    Auth0 logout endpoint

    Returns the Auth0 logout URL that clears the Auth0 session.

    Query params:
        return_to: Optional URL to redirect to after logout
    """
    if not settings.auth0_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auth0 authentication is not enabled"
        )

    # Default return URL
    return_url = return_to or "http://localhost:5173"

    # Build Auth0 logout URL
    params = {
        "client_id": settings.auth0_client_id,
        "returnTo": return_url,
    }

    logout_url = f"https://{settings.auth0_domain}/v2/logout?{urlencode(params)}"

    logger.info(f"Generated Auth0 logout URL, returning to: {return_url}")

    return {"logout_url": logout_url}


@router.get("/auth0/me")
async def auth0_user_info(access_token: str = Query(..., description="Access token")):
    """
    Get user information from Auth0

    Query params:
        access_token: Auth0 access token

    Returns:
        User profile information
    """
    if not settings.auth0_enabled:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Auth0 authentication is not enabled"
        )

    userinfo_url = f"https://{settings.auth0_domain}/userinfo"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to fetch user info"
                )

            return response.json()

    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to communicate with Auth0"
        )
