from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from app.models import AuditEvent, AuthenticatedIdentity, Permission, Role, User
from app.ports import (
    AuditSink,
    AuthorizationRepository,
    AuthorizationUnitOfWorkFactory,
    IdentityProvider,
)


class AuthenticationError(Exception):
    pass


class AuthorizationDeniedError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class AuthorizationService:
    def __init__(self, repository: AuthorizationRepository) -> None:
        self._repository = repository

    def resolve_user(self, identity: AuthenticatedIdentity) -> User:
        user = self._repository.get_user_by_identity(identity)
        if user is None:
            raise AuthenticationError("Identity is not assigned to an active user")
        return self.with_permissions(user)

    def with_permissions(self, user: User) -> User:
        permissions = self._repository.permissions_for_roles(user.roles)
        return user.model_copy(
            update={"permissions": sorted(permissions, key=lambda item: item.value)}
        )

    def list_users(self) -> list[User]:
        return [self.with_permissions(user) for user in self._repository.list_users()]

    def require(self, user: User, permission: Permission) -> None:
        if permission not in user.permissions:
            raise AuthorizationDeniedError(f"Missing permission: {permission.value}")


class RoleAssignmentService:
    def __init__(
        self,
        authorization: AuthorizationService,
        unit_of_work_factory: AuthorizationUnitOfWorkFactory,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._authorization = authorization
        self._unit_of_work_factory = unit_of_work_factory
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def assign_roles(
        self,
        actor: User,
        target_user_id: str,
        roles: list[Role],
        reason: str,
    ) -> User:
        self._authorization.require(actor, Permission.USERS_WRITE)
        unique_roles = list(dict.fromkeys(roles))
        with self._unit_of_work_factory() as unit_of_work:
            target = unit_of_work.repository.get_user(target_user_id)
            if target is None:
                raise UserNotFoundError(target_user_id)
            updated = unit_of_work.repository.update_user_roles(target_user_id, unique_roles)
            unit_of_work.audit_sink.record(
                AuditEvent(
                    action="roles.updated",
                    actor_id=actor.id,
                    target_type="user",
                    target_id=target_user_id,
                    reason=reason,
                    occurred_at=self._clock(),
                    previous_roles=target.roles,
                    new_roles=unique_roles,
                )
            )
            unit_of_work.commit()
        return self._authorization.with_permissions(updated)


@dataclass(frozen=True)
class SecurityContext:
    identity_provider: IdentityProvider
    authorization: AuthorizationService
    role_assignments: RoleAssignmentService
    audit_sink: AuditSink
