"""Authentication endpoints"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.security import create_access_token, verify_password

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


# OIDC endpoints (disabled by default)
# TODO: Implement OIDC flow when OIDC_ENABLED=true
# @router.get("/oidc/login")
# async def oidc_login():
#     """Redirect to OIDC provider"""
#     pass
#
# @router.get("/oidc/callback")
# async def oidc_callback(code: str):
#     """Handle OIDC callback"""
#     pass
