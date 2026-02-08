"""Authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user, CLAIMS_NAMESPACE
from app.core.config import settings
from app.db.session import get_db
from app.models import User

router = APIRouter()


class UserInfo(BaseModel):
    sub: str
    email: str | None
    name: str | None
    roles: list[str]
    permissions: list[str]
    candidate_id: str | None


class Auth0Config(BaseModel):
    domain: str
    client_id: str
    audience: str


@router.get("/config", response_model=Auth0Config)
def get_auth0_config():
    """Return Auth0 configuration for the frontend"""
    if not settings.auth0_domain or not settings.auth0_client_id or not settings.auth0_audience:
        raise HTTPException(status_code=503, detail="Auth0 not configured")
    return Auth0Config(
        domain=settings.auth0_domain,
        client_id=settings.auth0_client_id,
        audience=settings.auth0_audience,
    )


@router.get("/me", response_model=UserInfo)
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated user info, syncing with local DB"""
    sub = current_user["sub"]

    # Upsert user record
    user = db.query(User).filter(User.auth0_sub == sub).first()
    if not user:
        user = User(
            auth0_sub=sub,
            email=current_user.get("email") or "",
            role=_infer_role(current_user.get("roles", [])),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return UserInfo(
        sub=sub,
        email=current_user.get("email"),
        name=None,
        roles=current_user.get("roles", []),
        permissions=current_user.get("permissions", []),
        candidate_id=str(user.candidate_id) if user.candidate_id else None,
    )


def _infer_role(roles: list[str]) -> str:
    """Map Auth0 roles list to primary role"""
    if "superuser" in roles:
        return "superuser"
    if "project_manager" in roles:
        return "project_manager"
    return "candidate"
