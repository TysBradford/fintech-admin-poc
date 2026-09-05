from __future__ import annotations

from types import TracebackType
from typing import Protocol

from app.models import (
    AuditEvent,
    AuthenticatedIdentity,
    AuthenticationCredentials,
    Permission,
    Role,
    User,
)


class IdentityProvider(Protocol):
    def authenticate(self, credentials: AuthenticationCredentials) -> AuthenticatedIdentity: ...


class AuthorizationRepository(Protocol):
    def get_user_by_identity(self, identity: AuthenticatedIdentity) -> User | None: ...

    def get_user(self, user_id: str) -> User | None: ...

    def list_users(self) -> list[User]: ...

    def permissions_for_roles(self, roles: list[Role]) -> set[Permission]: ...

    def update_user_roles(self, user_id: str, roles: list[Role]) -> User: ...


class AuditSink(Protocol):
    def record(self, event: AuditEvent) -> None: ...


class AuthorizationUnitOfWork(Protocol):
    @property
    def repository(self) -> AuthorizationRepository: ...

    @property
    def audit_sink(self) -> AuditSink: ...

    def __enter__(self) -> AuthorizationUnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...


class AuthorizationUnitOfWorkFactory(Protocol):
    def __call__(self) -> AuthorizationUnitOfWork: ...


class KycDataSource(Protocol):
    def list_cases(self) -> list[dict[str, object]]: ...


class FeatureFlagProvider(Protocol):
    def list_flags(self) -> list[dict[str, object]]: ...

    def set_flag(self, flag_id: str, enabled: bool) -> dict[str, object]: ...


class PaymentsProvider(Protocol):
    def refund_summary(self) -> dict[str, object]: ...

    def list_refunds(self) -> list[dict[str, object]]: ...

    def approve_refund(
        self,
        refund_id: str,
        approver_id: str,
        reason: str,
    ) -> dict[str, object]: ...
