from __future__ import annotations

from types import TracebackType

from app.models import (
    AuditEvent,
    AuthenticatedIdentity,
    AuthenticationCredentials,
    Permission,
    Role,
    User,
)
from app.ports import AuthorizationRepository, AuthorizationUnitOfWork
from app.security import AuthenticationError

ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: set(Permission),
    Role.COMPLIANCE_ANALYST: {Permission.KYC_READ},
    Role.PRODUCT_MANAGER: {
        Permission.FEATURE_FLAGS_READ,
        Permission.FEATURE_FLAGS_WRITE,
    },
    Role.SUPPORT_LEAD: {
        Permission.REFUNDS_READ,
        Permission.REFUNDS_WRITE,
    },
}


DEMO_USERS: dict[str, User] = {
    "morgan": User(
        id="morgan",
        name="Morgan Lee",
        email="morgan.lee@example.internal",
        job_title="Platform Operations Director",
        department="Technology",
        roles=[Role.SUPER_ADMIN],
        avatar_color="#3157d5",
    ),
    "amina": User(
        id="amina",
        name="Amina Yusuf",
        email="amina.yusuf@example.internal",
        job_title="Senior Compliance Analyst",
        department="Compliance",
        roles=[Role.COMPLIANCE_ANALYST],
        avatar_color="#0c7c6d",
    ),
    "leo": User(
        id="leo",
        name="Leo Martins",
        email="leo.martins@example.internal",
        job_title="Product Manager",
        department="Product",
        roles=[Role.PRODUCT_MANAGER],
        avatar_color="#9a5b13",
    ),
    "priya": User(
        id="priya",
        name="Priya Shah",
        email="priya.shah@example.internal",
        job_title="Customer Support Lead",
        department="Customer Experience",
        roles=[Role.SUPPORT_LEAD],
        avatar_color="#813aa6",
    ),
}


class DemoIdentityProvider:
    def authenticate(self, credentials: AuthenticationCredentials) -> AuthenticatedIdentity:
        if credentials.identity_hint is None:
            raise AuthenticationError("Demo identity is required")
        return AuthenticatedIdentity(
            provider="demo",
            tenant_id="demo",
            subject=credentials.identity_hint,
        )


class DemoAuthorizationRepository:
    def __init__(self) -> None:
        self._users = {user_id: user.model_copy(deep=True) for user_id, user in DEMO_USERS.items()}

    def get_user_by_identity(self, identity: AuthenticatedIdentity) -> User | None:
        if identity.provider != "demo" or identity.tenant_id != "demo":
            return None
        return self.get_user(identity.subject)

    def get_user(self, user_id: str) -> User | None:
        user = self._users.get(user_id)
        return user.model_copy(deep=True) if user is not None else None

    def list_users(self) -> list[User]:
        return [user.model_copy(deep=True) for user in self._users.values()]

    def permissions_for_roles(self, roles: list[Role]) -> set[Permission]:
        permissions: set[Permission] = set()
        for role in roles:
            permissions.update(ROLE_PERMISSIONS[role])
        return permissions

    def update_user_roles(self, user_id: str, roles: list[Role]) -> User:
        user = self._users[user_id]
        updated = user.model_copy(update={"roles": roles}, deep=True)
        self._users[user_id] = updated
        return updated.model_copy(deep=True)

    def snapshot(self) -> dict[str, User]:
        return {user_id: user.model_copy(deep=True) for user_id, user in self._users.items()}

    def restore(self, users: dict[str, User]) -> None:
        self._users = {user_id: user.model_copy(deep=True) for user_id, user in users.items()}


class DemoAuditSink:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> list[AuditEvent]:
        return [event.model_copy(deep=True) for event in self._events]

    def record(self, event: AuditEvent) -> None:
        self._events.append(event.model_copy(deep=True))

    def snapshot(self) -> list[AuditEvent]:
        return self.events

    def restore(self, events: list[AuditEvent]) -> None:
        self._events = [event.model_copy(deep=True) for event in events]


class DemoAuthorizationUnitOfWork:
    def __init__(
        self,
        repository: DemoAuthorizationRepository,
        audit_sink: DemoAuditSink,
    ) -> None:
        self.repository: AuthorizationRepository = repository
        self.audit_sink = audit_sink
        self._demo_repository = repository
        self._demo_audit_sink = audit_sink
        self._user_snapshot: dict[str, User] = {}
        self._audit_snapshot: list[AuditEvent] = []
        self._committed = False

    def __enter__(self) -> AuthorizationUnitOfWork:
        self._user_snapshot = self._demo_repository.snapshot()
        self._audit_snapshot = self._demo_audit_sink.snapshot()
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None or not self._committed:
            self._demo_repository.restore(self._user_snapshot)
            self._demo_audit_sink.restore(self._audit_snapshot)

    def commit(self) -> None:
        self._committed = True


class DemoAuthorizationUnitOfWorkFactory:
    def __init__(
        self,
        repository: DemoAuthorizationRepository,
        audit_sink: DemoAuditSink,
    ) -> None:
        self._repository = repository
        self._audit_sink = audit_sink

    def __call__(self) -> AuthorizationUnitOfWork:
        return DemoAuthorizationUnitOfWork(self._repository, self._audit_sink)


class DemoKycDataSource:
    def list_cases(self) -> list[dict[str, object]]:
        return [
            {
                "id": "KYC-1048",
                "customer": "Nadia Okafor",
                "country": "GB",
                "risk": "High",
                "reason": "Document mismatch",
                "submitted": "12 min ago",
                "status": "Needs review",
            },
            {
                "id": "KYC-1047",
                "customer": "Mateo Silva",
                "country": "PT",
                "risk": "Medium",
                "reason": "Source of funds",
                "submitted": "34 min ago",
                "status": "In review",
            },
            {
                "id": "KYC-1045",
                "customer": "Elena Rossi",
                "country": "IT",
                "risk": "Low",
                "reason": "Address verification",
                "submitted": "1 hr ago",
                "status": "Needs review",
            },
            {
                "id": "KYC-1042",
                "customer": "Tariq Rahman",
                "country": "AE",
                "risk": "Medium",
                "reason": "Identity verification",
                "submitted": "2 hrs ago",
                "status": "Escalated",
            },
        ]


class DemoFeatureFlagProvider:
    def __init__(self) -> None:
        self.flags = [
            {
                "id": "instant-bank-verification",
                "name": "Instant bank verification",
                "description": "Use the new verification provider during account linking.",
                "enabled": True,
                "environment": "Production",
                "rollout": "100%",
                "owner": "Identity",
            },
            {
                "id": "refund-self-service",
                "name": "Refund self-service",
                "description": "Let eligible customers request refunds from the app.",
                "enabled": False,
                "environment": "Production",
                "rollout": "0%",
                "owner": "Payments",
            },
            {
                "id": "kyc-risk-signals-v2",
                "name": "KYC risk signals v2",
                "description": "Enable the second-generation risk scoring pipeline.",
                "enabled": True,
                "environment": "Staging",
                "rollout": "25%",
                "owner": "Compliance",
            },
        ]

    def list_flags(self) -> list[dict[str, object]]:
        return self.flags

    def set_flag(self, flag_id: str, enabled: bool) -> dict[str, object]:
        for flag in self.flags:
            if flag["id"] == flag_id:
                flag["enabled"] = enabled
                return flag
        raise KeyError(flag_id)


class DemoPaymentsProvider:
    def __init__(self) -> None:
        self.refunds = [
            {
                "id": "RF-8291",
                "customer": "Sophie Williams",
                "amount": "£1,249.00",
                "amount_minor": 124900,
                "reason": "Duplicate charge",
                "age": "18 min",
                "status": "Awaiting approval",
                "required_approvals": 2,
                "approval_count": 0,
                "approved_by": [],
            },
            {
                "id": "RF-8288",
                "customer": "Daniel Green",
                "amount": "£89.50",
                "amount_minor": 8950,
                "reason": "Service not received",
                "age": "42 min",
                "status": "Under review",
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
            },
            {
                "id": "RF-8283",
                "customer": "Chloe Adams",
                "amount": "£425.20",
                "amount_minor": 42520,
                "reason": "Merchant dispute",
                "age": "1 hr",
                "status": "Awaiting approval",
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
            },
        ]

    def refund_summary(self) -> dict[str, object]:
        pending = [refund for refund in self.refunds if refund["status"] != "Approved"]
        pending_value = 0
        for refund in pending:
            amount_minor = refund["amount_minor"]
            if not isinstance(amount_minor, int):
                raise TypeError("Refund amount data is invalid")
            pending_value += amount_minor
        return {
            "pending_count": len(pending),
            "pending_value": f"£{pending_value / 100:,.2f}",
            "processed_today": 23 + len(self.refunds) - len(pending),
            "approval_rate": "91.4%",
        }

    def list_refunds(self) -> list[dict[str, object]]:
        return self.refunds

    def approve_refund(
        self,
        refund_id: str,
        approver_id: str,
        reason: str,
    ) -> dict[str, object]:
        for refund in self.refunds:
            if refund["id"] != refund_id:
                continue

            approved_by = refund["approved_by"]
            if not isinstance(approved_by, list):
                raise TypeError("Refund approval data is invalid")
            if approver_id in approved_by:
                raise PermissionError("A distinct approver is required")

            required_approvals = refund["required_approvals"]
            if not isinstance(required_approvals, int):
                raise TypeError("Refund approval policy is invalid")
            approved_by.append(approver_id)
            refund["approval_count"] = len(approved_by)
            refund["last_approval_reason"] = reason
            if len(approved_by) >= required_approvals:
                refund["status"] = "Approved"
            else:
                refund["status"] = "Awaiting second approval"
            return refund

        raise KeyError(refund_id)
