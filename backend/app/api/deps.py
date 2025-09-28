from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped session that closes when the request finishes."""

    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


@dataclass(frozen=True, slots=True)
class UserIdentity:
    """Primitive user identity decoded from the access token."""

    user_id: UUID


@dataclass(slots=True)
class UserContext:
    """Context object shared between dependencies and handlers.

    Note: we only cache primitive user attributes here to avoid detached ORM
    instances when the handler awaits downstream work.
    """

    user_id: UUID
    email: str
    is_active: bool
    is_superuser: bool
    db: Session


def _decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return TokenPayload(**payload)
    except (InvalidTokenError, ValidationError) as exc:  # pragma: no cover - parity guard
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        ) from exc


def _extract_user_id(token_data: TokenPayload) -> UUID:
    if token_data.sub is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    try:
        return UUID(token_data.sub)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed token subject",
        ) from exc


def _load_user(session: Session, token: str) -> User:
    token_data = _decode_token(token)
    user_id = _extract_user_id(token_data)
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """Original DI helper retained for existing routes."""

    return _load_user(session, token)


def build_user_context(session: Session, token: str) -> UserContext:
    user = _load_user(session, token)
    return UserContext(
        user_id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        db=session,
    )


def get_current_active_user_context(
    session: SessionDep, token: TokenDep
) -> UserContext:
    """Dependency that exercises the classic DI pattern used in the blog post."""

    return build_user_context(session, token)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_user_identity(token: TokenDep) -> UserIdentity:
    token_data = _decode_token(token)
    return UserIdentity(user_id=_extract_user_id(token_data))


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def extract_bearer_token(request: Request) -> str:
    """Pull the bearer token straight off the request for inline experiments."""

    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials


def build_user_context_from_identity(
    session: Session, identity: UserIdentity
) -> UserContext:
    user = session.get(User, identity.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return UserContext(
        user_id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        db=session,
    )


def pre_handler_connection_probe(session: SessionDep) -> None:
    """Simulate middleware that grabs a connection before the handler runs."""

    # Touch the database so the connection is checked out prior to handler
    # execution. The goal is to mirror real authentication/observability
    # middlewares that perform a lightweight query.
    session.exec(select(User.id)).first()
