from collections.abc import Callable
from typing import Annotated, cast

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models import AuthenticationCredentials, Permission, User
from app.security import (
    AuthenticationError,
    AuthorizationDeniedError,
    SecurityContext,
)

bearer_scheme = HTTPBearer(auto_error=False)


def get_security_context(request: Request) -> SecurityContext:
    return cast(SecurityContext, request.app.state.security)


def get_current_user(
    security: Annotated[SecurityContext, Depends(get_security_context)],
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    x_demo_user: Annotated[str | None, Header()] = None,
) -> User:
    try:
        identity = security.identity_provider.authenticate(
            AuthenticationCredentials(
                authorization=(
                    f"{bearer.scheme} {bearer.credentials}" if bearer is not None else None
                ),
                identity_hint=x_demo_user,
            )
        )
        return security.authorization.resolve_user(identity)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error


def require_permission(
    permission: Permission,
) -> Callable[[SecurityContext, User], User]:
    def dependency(
        security: Annotated[SecurityContext, Depends(get_security_context)],
        user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        try:
            security.authorization.require(user, permission)
        except AuthorizationDeniedError as error:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(error),
            ) from error
        return user

    return dependency
