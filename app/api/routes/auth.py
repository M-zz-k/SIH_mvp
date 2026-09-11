from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.db_models import User
from app.models.schemas import LoginRequest, TokenResponse, UserOut, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Public self-registration.  Role is ALWAYS 'inspector' — nobody can
    self-elevate to supervisor/admin via this endpoint.
    Use POST /auth/promote (admin-only) to change roles after the fact.
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=UserRole.INSPECTOR.value,   # hardcoded — not taken from request
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        email=user.email,
        role=UserRole(user.role.value if hasattr(user.role, "value") else user.role),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    role_value = user.role.value if hasattr(user.role, "value") else user.role
    token = create_access_token(subject=user.email, role=role_value)
    return TokenResponse(access_token=token, role=UserRole(role_value))


# ---------------------------------------------------------------------------
# Admin-only role management
# ---------------------------------------------------------------------------

class PromoteRequest(BaseModel):
    """Payload for the admin-only promote/demote endpoints."""
    email: str
    new_role: UserRole


@router.post(
    "/promote",
    response_model=UserOut,
    summary="Admin-only: promote a user to supervisor or admin",
)
def promote_user(
    payload: PromoteRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Lets an admin elevate any existing user to 'supervisor' or 'admin'.
    Returns 400 if new_role is 'inspector' — use POST /auth/demote for that.
    """
    if payload.new_role == UserRole.INSPECTOR:
        raise HTTPException(
            status_code=400,
            detail="Promote endpoint is for supervisor/admin only. "
                   "Use POST /auth/demote to walk back a promotion to inspector.",
        )

    target = db.query(User).filter(User.email == payload.email).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.role = payload.new_role.value
    db.commit()
    db.refresh(target)
    return UserOut(
        id=target.id,
        email=target.email,
        role=UserRole(
            target.role.value if hasattr(target.role, "value") else target.role
        ),
    )


# ---------------------------------------------------------------------------
# Current-user info
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserOut,
    summary="Return the currently authenticated user's own profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Any authenticated user can call this to retrieve their own id, email,
    and role without needing to decode the JWT client-side.
    Returns 401 if the token is missing or invalid.
    """
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        role=UserRole(
            current_user.role.value if hasattr(current_user.role, "value") else current_user.role
        ),
    )


# ---------------------------------------------------------------------------
# Admin-only demotion (inverse of /promote)
# ---------------------------------------------------------------------------

@router.post(
    "/demote",
    response_model=UserOut,
    summary="Admin-only: demote a user back to inspector",
)
def demote_user(
    payload: PromoteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.ADMIN)),
):
    """
    Walks back a promotion — sets any user's role back to 'inspector'.
    Only accepts new_role == inspector; use POST /auth/promote for
    supervisor/admin elevations (keeps the two endpoints non-overlapping).

    Safety: an admin cannot demote themselves if they are the last remaining
    admin in the system — that would re-introduce the bootstrap lock-out
    that seed_admin() was added to fix.
    """
    if payload.new_role != UserRole.INSPECTOR:
        raise HTTPException(
            status_code=400,
            detail="Demote endpoint only accepts new_role='inspector'. "
                   "Use POST /auth/promote to change roles to supervisor/admin.",
        )

    target = db.query(User).filter(User.email == payload.email).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Last-admin guard: if the target IS an admin and is the same person
    # calling the endpoint (self-demotion), block it when they're the only admin.
    from app.models.db_models import UserRoleDB
    target_is_admin = (
        target.role == UserRoleDB.admin
        or (hasattr(target.role, "value") and target.role.value == UserRole.ADMIN.value)
    )
    if target_is_admin:
        admin_count = db.query(User).filter(User.role == UserRoleDB.admin).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last remaining admin — "
                       "the system would have no admin left. "
                       "Promote another user to admin first.",
            )

    target.role = UserRole.INSPECTOR.value
    db.commit()
    db.refresh(target)
    return UserOut(
        id=target.id,
        email=target.email,
        role=UserRole(
            target.role.value if hasattr(target.role, "value") else target.role
        ),
    )
