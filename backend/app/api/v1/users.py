"""User management endpoints (superuser only)"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import RequireSuperuser, PERM_MANAGE_USERS, require_permission
from app.db.session import get_db
from app.models import Candidate, User

router = APIRouter()

VALID_ROLES = {"superuser", "project_manager", "candidate"}


class UserResponse(BaseModel):
    id: str
    auth0_sub: str
    email: str
    name: Optional[str]
    role: str
    candidate_id: Optional[str]
    created_at: str


class UserUpdate(BaseModel):
    role: Optional[str] = None
    candidate_id: Optional[str] = None
    name: Optional[str] = None


class UserCreate(BaseModel):
    auth0_sub: str
    email: str
    role: str = "candidate"
    candidate_id: Optional[str] = None
    name: Optional[str] = None


@router.get("/", response_model=List[UserResponse])
def list_users(
    _user: dict = Depends(require_permission(PERM_MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    """List all users"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [_to_response(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    _user: dict = Depends(require_permission(PERM_MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    """Get user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    req: UserUpdate,
    _user: dict = Depends(require_permission(PERM_MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    """Update user role or candidate link"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.role is not None:
        if req.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {VALID_ROLES}")
        user.role = req.role

    if req.candidate_id is not None:
        if req.candidate_id:
            candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
            if not candidate:
                raise HTTPException(status_code=400, detail="Candidate not found for candidate_id")
        user.candidate_id = req.candidate_id

    if req.name is not None:
        user.name = req.name

    db.commit()
    db.refresh(user)
    return _to_response(user)


@router.post("/", response_model=UserResponse)
def create_user(
    req: UserCreate,
    _user: dict = Depends(require_permission(PERM_MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    """Create a new user mapping."""
    if req.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {VALID_ROLES}")

    existing = db.query(User).filter(User.auth0_sub == req.auth0_sub).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this auth0_sub already exists")

    candidate_id = None
    if req.candidate_id:
        candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=400, detail="Candidate not found for candidate_id")
        candidate_id = req.candidate_id

    user = User(
        auth0_sub=req.auth0_sub.strip(),
        email=req.email.strip().lower(),
        role=req.role,
        candidate_id=candidate_id,
        name=req.name.strip() if req.name else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_response(user)


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: dict = Depends(require_permission(PERM_MANAGE_USERS)),
    db: Session = Depends(get_db),
):
    """Delete user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prevent self-deletion
    if user.auth0_sub == current_user.get("sub"):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    db.delete(user)
    db.commit()
    return {"deleted": True, "id": user_id}


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        auth0_sub=user.auth0_sub,
        email=user.email,
        name=user.name,
        role=user.role,
        candidate_id=str(user.candidate_id) if user.candidate_id else None,
        created_at=user.created_at.isoformat(),
    )
