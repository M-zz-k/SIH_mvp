"""
Reusable FastAPI dependencies: DB session, current user, role checks.
Import these into route files instead of re-writing auth logic per route.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.db_models import User
from app.models.schemas import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_error

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if user is None:
        raise credentials_error
    return user


def require_role(*allowed_roles: UserRole):
    """
    Usage in a route:
        @router.delete(...)
        def delete_thing(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
    """

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return user

    return checker
