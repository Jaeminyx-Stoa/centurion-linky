import uuid

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import clinic_id_var, user_id_var
from app.core.security import decode_token
from app.models.user import User
from app.schemas.pagination import PaginationParams

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedError("Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError()
    except InvalidTokenError:
        raise UnauthorizedError()

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise UnauthorizedError()

    clinic_id_var.set(str(user.clinic_id))
    user_id_var.set(str(user.id))

    return user


def get_pagination(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> PaginationParams:
    return PaginationParams(limit=limit, offset=offset)


def require_role(*roles: str):
    """Dependency factory: restrict endpoint access to specific user roles."""

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("Insufficient permissions")
        return current_user

    return _check
