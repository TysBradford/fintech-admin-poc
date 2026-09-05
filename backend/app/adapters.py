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
    Role.COMPLIANCE_ANALYST: {Permission.KYC_READ, Permission.KYC_WRITE},
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
        location="London",
        last_active="Online now",
        access_review="Due 30 Sep 2026",
        mfa_status="FIDO2 security key",
        roles=[Role.SUPER_ADMIN],
        avatar_color="#3157d5",
    ),
    "amina": User(
        id="amina",
        name="Amina Yusuf",
        email="amina.yusuf@example.internal",
        job_title="Senior Compliance Analyst",
        department="Compliance",
        location="London",
        last_active="8 min ago",
        access_review="Due 14 Oct 2026",
        mfa_status="Authenticator app",
        roles=[Role.COMPLIANCE_ANALYST],
        avatar_color="#0c7c6d",
    ),
    "leo": User(
        id="leo",
        name="Leo Martins",
        email="leo.martins@example.internal",
        job_title="Product Manager",
        department="Product",
        location="Lisbon",
        last_active="21 min ago",
        access_review="Due 30 Sep 2026",
        mfa_status="Authenticator app",
        roles=[Role.PRODUCT_MANAGER],
        avatar_color="#9a5b13",
    ),
    "priya": User(
        id="priya",
        name="Priya Shah",
        email="priya.shah@example.internal",
        job_title="Customer Support Lead",
        department="Customer Experience",
        location="Manchester",
        last_active="Online now",
        access_review="Due 21 Oct 2026",
        mfa_status="FIDO2 security key",
        roles=[Role.SUPPORT_LEAD],
        avatar_color="#813aa6",
    ),
    "david": User(
        id="david",
        name="David Chen",
        email="david.chen@example.internal",
        job_title="Compliance Analyst",
        department="Compliance",
        location="London",
        last_active="36 min ago",
        access_review="Due 14 Oct 2026",
        mfa_status="Authenticator app",
        roles=[Role.COMPLIANCE_ANALYST],
        avatar_color="#2f6f91",
    ),
    "maya": User(
        id="maya",
        name="Maya Patel",
        email="maya.patel@example.internal",
        job_title="Refund Operations Specialist",
        department="Customer Experience",
        location="Birmingham",
        last_active="12 min ago",
        access_review="Due 21 Oct 2026",
        mfa_status="Authenticator app",
        roles=[Role.SUPPORT_LEAD],
        avatar_color="#a54f77",
    ),
    "elena": User(
        id="elena",
        name="Elena Rossi",
        email="elena.rossi@example.internal",
        job_title="Senior Product Manager",
        department="Product",
        location="Milan",
        last_active="1 hr ago",
        access_review="Due 30 Sep 2026",
        mfa_status="FIDO2 security key",
        roles=[Role.PRODUCT_MANAGER],
        avatar_color="#b06727",
    ),
    "jon": User(
        id="jon",
        name="Jon Bell",
        email="jon.bell@example.internal",
        job_title="Security Engineering Lead",
        department="Security",
        location="London",
        last_active="Yesterday",
        access_review="Due 12 Sep 2026",
        mfa_status="FIDO2 security key",
        roles=[Role.SUPER_ADMIN],
        avatar_color="#3d568d",
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
    def __init__(self) -> None:
        self.cases: list[dict[str, object]] = [
            {
                "id": "KYC-1086",
                "customer": "Nadia Okafor",
                "customer_id": "CUS-78421",
                "country": "GB",
                "entity_type": "Individual",
                "risk": "High",
                "reason": "Document mismatch",
                "signals": ["Document mismatch", "Device risk"],
                "submitted": "12 min ago",
                "sla": "48 min remaining",
                "sla_state": "On track",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Manual review requested",
                        "actor": "Identity verification service",
                        "at": "12 min ago",
                    },
                    {
                        "action": "Passport image mismatch detected",
                        "actor": "Automated controls",
                        "at": "13 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1085",
                "customer": "Mateo Silva",
                "customer_id": "CUS-78397",
                "country": "PT",
                "entity_type": "Individual",
                "risk": "Medium",
                "reason": "Source of funds",
                "signals": ["High initial deposit"],
                "submitted": "34 min ago",
                "sla": "1 hr 26 min remaining",
                "sla_state": "On track",
                "status": "In review",
                "assignee_id": "amina",
                "assignee": "Amina Yusuf",
                "audit": [
                    {
                        "action": "Assigned to Amina Yusuf",
                        "actor": "Queue routing",
                        "at": "21 min ago",
                    },
                    {
                        "action": "Bank statement received",
                        "actor": "Mateo Silva",
                        "at": "34 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1084",
                "customer": "Elena Rossi",
                "customer_id": "CUS-78375",
                "country": "IT",
                "entity_type": "Individual",
                "risk": "Low",
                "reason": "Address verification",
                "signals": ["Address recency"],
                "submitted": "51 min ago",
                "sla": "3 hr 9 min remaining",
                "sla_state": "On track",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Proof of address requires review",
                        "actor": "Automated controls",
                        "at": "51 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1083",
                "customer": "Tariq Rahman",
                "customer_id": "CUS-78342",
                "country": "AE",
                "entity_type": "Individual",
                "risk": "High",
                "reason": "Sanctions name match",
                "signals": ["Potential PEP", "Name screening match"],
                "submitted": "1 hr 8 min ago",
                "sla": "Breached by 8 min",
                "sla_state": "Breached",
                "status": "Escalated",
                "assignee_id": "amina",
                "assignee": "Amina Yusuf",
                "audit": [
                    {
                        "action": "Escalated to financial crime",
                        "actor": "Amina Yusuf",
                        "at": "18 min ago",
                    },
                    {
                        "action": "Potential screening match detected",
                        "actor": "Screening service",
                        "at": "1 hr 8 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1082",
                "customer": "Jun Park",
                "customer_id": "CUS-78318",
                "country": "KR",
                "entity_type": "Individual",
                "risk": "Medium",
                "reason": "Identity verification",
                "signals": ["Liveness retry"],
                "submitted": "1 hr 22 min ago",
                "sla": "38 min remaining",
                "sla_state": "Due soon",
                "status": "In review",
                "assignee_id": "david",
                "assignee": "David Chen",
                "audit": [
                    {
                        "action": "Liveness evidence opened",
                        "actor": "David Chen",
                        "at": "9 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1081",
                "customer": "Willow & Finch Ltd",
                "customer_id": "BUS-21891",
                "country": "GB",
                "entity_type": "Business",
                "risk": "High",
                "reason": "Beneficial ownership",
                "signals": ["Complex ownership", "Offshore shareholder"],
                "submitted": "1 hr 37 min ago",
                "sla": "23 min remaining",
                "sla_state": "Due soon",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Ownership chart uploaded",
                        "actor": "Willow & Finch Ltd",
                        "at": "1 hr 37 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1080",
                "customer": "Camila Torres",
                "customer_id": "CUS-78295",
                "country": "ES",
                "entity_type": "Individual",
                "risk": "Medium",
                "reason": "Source of wealth",
                "signals": ["Occupation mismatch"],
                "submitted": "1 hr 54 min ago",
                "sla": "6 min remaining",
                "sla_state": "Due soon",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Enhanced due diligence requested",
                        "actor": "Risk engine",
                        "at": "1 hr 54 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1079",
                "customer": "Samir Haddad",
                "customer_id": "CUS-78274",
                "country": "FR",
                "entity_type": "Individual",
                "risk": "Low",
                "reason": "Document expiry",
                "signals": ["Document near expiry"],
                "submitted": "2 hr 14 min ago",
                "sla": "1 hr 46 min remaining",
                "sla_state": "On track",
                "status": "In review",
                "assignee_id": "amina",
                "assignee": "Amina Yusuf",
                "audit": [
                    {
                        "action": "Replacement document requested",
                        "actor": "Amina Yusuf",
                        "at": "47 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1078",
                "customer": "Northbank Studio GmbH",
                "customer_id": "BUS-21880",
                "country": "DE",
                "entity_type": "Business",
                "risk": "Medium",
                "reason": "Company registry",
                "signals": ["Registry data mismatch"],
                "submitted": "2 hr 31 min ago",
                "sla": "Breached by 31 min",
                "sla_state": "Breached",
                "status": "Escalated",
                "assignee_id": "david",
                "assignee": "David Chen",
                "audit": [
                    {
                        "action": "Registry mismatch escalated",
                        "actor": "David Chen",
                        "at": "1 hr ago",
                    },
                ],
            },
            {
                "id": "KYC-1077",
                "customer": "Grace Mensah",
                "customer_id": "CUS-78240",
                "country": "GH",
                "entity_type": "Individual",
                "risk": "Medium",
                "reason": "Address verification",
                "signals": ["Geolocation mismatch"],
                "submitted": "2 hr 46 min ago",
                "sla": "1 hr 14 min remaining",
                "sla_state": "On track",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Address evidence queued",
                        "actor": "Identity verification service",
                        "at": "2 hr 46 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1076",
                "customer": "Oliver Brooks",
                "customer_id": "CUS-78211",
                "country": "GB",
                "entity_type": "Individual",
                "risk": "High",
                "reason": "Adverse media",
                "signals": ["Adverse media", "Industry risk"],
                "submitted": "3 hr 2 min ago",
                "sla": "Breached by 2 hr 2 min",
                "sla_state": "Breached",
                "status": "Escalated",
                "assignee_id": "amina",
                "assignee": "Amina Yusuf",
                "audit": [
                    {
                        "action": "Senior review requested",
                        "actor": "Amina Yusuf",
                        "at": "2 hr ago",
                    },
                ],
            },
            {
                "id": "KYC-1075",
                "customer": "Priyanka Nair",
                "customer_id": "CUS-78189",
                "country": "IN",
                "entity_type": "Individual",
                "risk": "Low",
                "reason": "Identity verification",
                "signals": ["Manual quality check"],
                "submitted": "3 hr 24 min ago",
                "sla": "36 min remaining",
                "sla_state": "Due soon",
                "status": "In review",
                "assignee_id": "david",
                "assignee": "David Chen",
                "audit": [
                    {
                        "action": "Document image opened",
                        "actor": "David Chen",
                        "at": "33 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1074",
                "customer": "Arc & Harbor SAS",
                "customer_id": "BUS-21861",
                "country": "FR",
                "entity_type": "Business",
                "risk": "Medium",
                "reason": "Director verification",
                "signals": ["Director document missing"],
                "submitted": "3 hr 51 min ago",
                "sla": "9 min remaining",
                "sla_state": "Due soon",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Director evidence requested",
                        "actor": "Business onboarding",
                        "at": "3 hr 51 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1073",
                "customer": "Amelia Wright",
                "customer_id": "CUS-78154",
                "country": "GB",
                "entity_type": "Individual",
                "risk": "Low",
                "reason": "Duplicate account",
                "signals": ["Possible duplicate"],
                "submitted": "4 hr 10 min ago",
                "sla": "Breached by 10 min",
                "sla_state": "Breached",
                "status": "In review",
                "assignee_id": "amina",
                "assignee": "Amina Yusuf",
                "audit": [
                    {
                        "action": "Related account comparison started",
                        "actor": "Amina Yusuf",
                        "at": "1 hr ago",
                    },
                ],
            },
            {
                "id": "KYC-1072",
                "customer": "Theo van Dijk",
                "customer_id": "CUS-78126",
                "country": "NL",
                "entity_type": "Individual",
                "risk": "Medium",
                "reason": "Source of funds",
                "signals": ["Crypto proceeds declared"],
                "submitted": "4 hr 28 min ago",
                "sla": "Breached by 2 hr 28 min",
                "sla_state": "Breached",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Supporting evidence received",
                        "actor": "Theo van Dijk",
                        "at": "4 hr 28 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1071",
                "customer": "Blue Ember OÜ",
                "customer_id": "BUS-21837",
                "country": "EE",
                "entity_type": "Business",
                "risk": "High",
                "reason": "Business activity",
                "signals": ["Restricted industry", "Cross-border activity"],
                "submitted": "5 hr 6 min ago",
                "sla": "Breached by 4 hr 6 min",
                "sla_state": "Breached",
                "status": "Escalated",
                "assignee_id": "amina",
                "assignee": "Amina Yusuf",
                "audit": [
                    {
                        "action": "Compliance manager review requested",
                        "actor": "Amina Yusuf",
                        "at": "2 hr ago",
                    },
                ],
            },
            {
                "id": "KYC-1070",
                "customer": "Luca Bianchi",
                "customer_id": "CUS-78099",
                "country": "IT",
                "entity_type": "Individual",
                "risk": "Low",
                "reason": "Document quality",
                "signals": ["Image glare"],
                "submitted": "5 hr 42 min ago",
                "sla": "Breached by 1 hr 42 min",
                "sla_state": "Breached",
                "status": "Needs review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "audit": [
                    {
                        "action": "Manual document check requested",
                        "actor": "Identity verification service",
                        "at": "5 hr 42 min ago",
                    },
                ],
            },
            {
                "id": "KYC-1069",
                "customer": "Maya Thompson",
                "customer_id": "CUS-78072",
                "country": "US",
                "entity_type": "Individual",
                "risk": "Medium",
                "reason": "Tax residency",
                "signals": ["Multiple tax residencies"],
                "submitted": "6 hr 4 min ago",
                "sla": "Breached by 4 hr 4 min",
                "sla_state": "Breached",
                "status": "In review",
                "assignee_id": "david",
                "assignee": "David Chen",
                "audit": [
                    {
                        "action": "Tax declaration under review",
                        "actor": "David Chen",
                        "at": "2 hr ago",
                    },
                ],
            },
        ]

    def list_cases(self) -> list[dict[str, object]]:
        return self.cases

    def assign_case(
        self,
        case_id: str,
        assignee_id: str,
        assignee_name: str,
        reason: str,
    ) -> dict[str, object]:
        for case in self.cases:
            if case["id"] != case_id:
                continue
            case["assignee_id"] = assignee_id
            case["assignee"] = assignee_name
            case["status"] = "In review"
            audit = case["audit"]
            if not isinstance(audit, list):
                raise TypeError("KYC audit data is invalid")
            audit.insert(
                0,
                {
                    "action": f"Assigned to {assignee_name}: {reason}",
                    "actor": assignee_name,
                    "at": "Just now",
                },
            )
            return case
        raise KeyError(case_id)


class DemoFeatureFlagProvider:
    def __init__(self) -> None:
        self.flags: list[dict[str, object]] = [
            {
                "id": "instant-bank-verification",
                "name": "Instant bank verification",
                "description": "Use the new verification provider during account linking.",
                "enabled": True,
                "environment": "Production",
                "rollout": "100%",
                "owner": "Identity",
                "owner_contact": "Elena Rossi",
                "flag_type": "Release",
                "risk": "Elevated",
                "expires": "30 Nov 2026",
                "last_changed": "2 days ago",
                "change_ticket": "PLAT-1842",
                "audit": [
                    {
                        "action": "Rollout increased from 50% to 100%",
                        "actor": "Elena Rossi",
                        "at": "2 days ago",
                    },
                    {
                        "action": "Production approval recorded",
                        "actor": "Morgan Lee",
                        "at": "3 days ago",
                    },
                ],
            },
            {
                "id": "refund-self-service",
                "name": "Refund self-service",
                "description": "Let eligible customers request refunds from the app.",
                "enabled": False,
                "environment": "Production",
                "rollout": "0%",
                "owner": "Payments",
                "owner_contact": "Leo Martins",
                "flag_type": "Release",
                "risk": "Elevated",
                "expires": "15 Dec 2026",
                "last_changed": "5 days ago",
                "change_ticket": "PAY-991",
                "audit": [
                    {
                        "action": "Flag disabled after support readiness review",
                        "actor": "Leo Martins",
                        "at": "5 days ago",
                    },
                ],
            },
            {
                "id": "kyc-risk-signals-v2",
                "name": "KYC risk signals v2",
                "description": "Enable the second-generation risk scoring pipeline.",
                "enabled": True,
                "environment": "Staging",
                "rollout": "25%",
                "owner": "Compliance",
                "owner_contact": "Amina Yusuf",
                "flag_type": "Experiment",
                "risk": "Elevated",
                "expires": "18 Sep 2026",
                "last_changed": "4 hours ago",
                "change_ticket": "COMP-447",
                "audit": [
                    {
                        "action": "Staging rollout increased to 25%",
                        "actor": "Amina Yusuf",
                        "at": "4 hours ago",
                    },
                ],
            },
            {
                "id": "cards-3ds-step-up",
                "name": "3DS step-up routing",
                "description": "Apply the updated step-up policy for higher-risk card payments.",
                "enabled": True,
                "environment": "Production",
                "rollout": "75%",
                "owner": "Cards",
                "owner_contact": "Leo Martins",
                "flag_type": "Release",
                "risk": "Elevated",
                "expires": "31 Oct 2026",
                "last_changed": "Yesterday",
                "change_ticket": "CARD-2208",
                "audit": [
                    {
                        "action": "Rollout increased from 50% to 75%",
                        "actor": "Leo Martins",
                        "at": "Yesterday",
                    },
                ],
            },
            {
                "id": "outbound-transfer-pause",
                "name": "Outbound transfer pause",
                "description": "Emergency control to pause outbound bank transfers.",
                "enabled": False,
                "environment": "Production",
                "rollout": "0%",
                "owner": "Payments",
                "owner_contact": "Morgan Lee",
                "flag_type": "Kill switch",
                "risk": "Critical",
                "expires": "No expiry",
                "last_changed": "28 days ago",
                "change_ticket": "INC-731",
                "audit": [
                    {
                        "action": "Quarterly control test completed",
                        "actor": "Morgan Lee",
                        "at": "28 days ago",
                    },
                ],
            },
            {
                "id": "home-balance-insights",
                "name": "Balance insights",
                "description": "Show customers weekly balance and spending insights.",
                "enabled": True,
                "environment": "Production",
                "rollout": "10%",
                "owner": "Money Management",
                "owner_contact": "Elena Rossi",
                "flag_type": "Experiment",
                "risk": "Standard",
                "expires": "25 Sep 2026",
                "last_changed": "3 days ago",
                "change_ticket": "GROW-638",
                "audit": [
                    {
                        "action": "Experiment started at 10%",
                        "actor": "Elena Rossi",
                        "at": "3 days ago",
                    },
                ],
            },
        ]

    def list_flags(self) -> list[dict[str, object]]:
        return self.flags

    def set_flag(
        self,
        flag_id: str,
        enabled: bool,
        actor: str,
        reason: str,
    ) -> dict[str, object]:
        for flag in self.flags:
            if flag["id"] == flag_id:
                flag["enabled"] = enabled
                flag["last_changed"] = "Just now"
                audit = flag["audit"]
                if not isinstance(audit, list):
                    raise TypeError("Feature flag audit data is invalid")
                audit.insert(
                    0,
                    {
                        "action": f"Flag {'enabled' if enabled else 'disabled'}: {reason}",
                        "actor": actor,
                        "at": "Just now",
                    },
                )
                return flag
        raise KeyError(flag_id)


class DemoPaymentsProvider:
    def __init__(self) -> None:
        self.refunds: list[dict[str, object]] = [
            {
                "id": "RF-8291",
                "customer": "Sophie Williams",
                "customer_id": "CUS-76184",
                "amount": "£1,249.00",
                "amount_minor": 124900,
                "reason": "Duplicate charge",
                "channel": "Card payment",
                "payment_method": "Visa ···· 4821",
                "age": "18 min",
                "sla": "42 min remaining",
                "sla_state": "Due soon",
                "status": "Awaiting approval",
                "assignee_id": "priya",
                "assignee": "Priya Shah",
                "risk_flags": ["High value", "Duplicate payment signal"],
                "required_approvals": 2,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "Refund request created",
                        "actor": "Customer support workflow",
                        "at": "18 min ago",
                    },
                    {
                        "action": "Dual approval control applied",
                        "actor": "Refund policy engine",
                        "at": "18 min ago",
                    },
                ],
            },
            {
                "id": "RF-8288",
                "customer": "Daniel Green",
                "customer_id": "CUS-76095",
                "amount": "£89.50",
                "amount_minor": 8950,
                "reason": "Service not received",
                "channel": "Bank transfer",
                "payment_method": "Account ···· 1049",
                "age": "42 min",
                "sla": "2 hr 18 min remaining",
                "sla_state": "On track",
                "status": "Under review",
                "assignee_id": "maya",
                "assignee": "Maya Patel",
                "risk_flags": [],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "Merchant evidence requested",
                        "actor": "Maya Patel",
                        "at": "14 min ago",
                    },
                ],
            },
            {
                "id": "RF-8283",
                "customer": "Chloe Adams",
                "customer_id": "CUS-76044",
                "amount": "£425.20",
                "amount_minor": 42520,
                "reason": "Merchant dispute",
                "channel": "Card payment",
                "payment_method": "Mastercard ···· 9374",
                "age": "1 hr",
                "sla": "2 hr remaining",
                "sla_state": "On track",
                "status": "Awaiting approval",
                "assignee_id": None,
                "assignee": "Unassigned",
                "risk_flags": ["Repeat refund request"],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "Refund request submitted",
                        "actor": "Customer support workflow",
                        "at": "1 hr ago",
                    },
                ],
            },
            {
                "id": "RF-8279",
                "customer": "Aarav Mehta",
                "customer_id": "CUS-75998",
                "amount": "£32.00",
                "amount_minor": 3200,
                "reason": "Cash withdrawal fee",
                "channel": "Cash withdrawal",
                "payment_method": "Debit card ···· 1182",
                "age": "1 hr 16 min",
                "sla": "1 hr 44 min remaining",
                "sla_state": "On track",
                "status": "Under review",
                "assignee_id": "priya",
                "assignee": "Priya Shah",
                "risk_flags": [],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "ATM trace requested",
                        "actor": "Priya Shah",
                        "at": "22 min ago",
                    },
                ],
            },
            {
                "id": "RF-8272",
                "customer": "Hannah Müller",
                "customer_id": "CUS-75931",
                "amount": "£607.00",
                "amount_minor": 60700,
                "reason": "Card purchase reversed",
                "channel": "Card payment",
                "payment_method": "Visa ···· 7740",
                "age": "1 hr 49 min",
                "sla": "11 min remaining",
                "sla_state": "Due soon",
                "status": "Evidence requested",
                "assignee_id": "maya",
                "assignee": "Maya Patel",
                "risk_flags": ["Cross-border payment"],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "Receipt requested from customer",
                        "actor": "Maya Patel",
                        "at": "39 min ago",
                    },
                ],
            },
            {
                "id": "RF-8268",
                "customer": "Noah Johnson",
                "customer_id": "CUS-75884",
                "amount": "£2,840.00",
                "amount_minor": 284000,
                "reason": "Incorrect beneficiary",
                "channel": "Bank transfer",
                "payment_method": "Account ···· 6218",
                "age": "2 hr 8 min",
                "sla": "Breached by 8 min",
                "sla_state": "Breached",
                "status": "Awaiting second approval",
                "assignee_id": "priya",
                "assignee": "Priya Shah",
                "risk_flags": ["High value", "Beneficiary changed recently"],
                "required_approvals": 2,
                "approval_count": 1,
                "approved_by": ["maya"],
                "audit": [
                    {
                        "action": "First approval recorded",
                        "actor": "Maya Patel",
                        "at": "27 min ago",
                    },
                    {
                        "action": "Payment recovery confirmed",
                        "actor": "Payments operations",
                        "at": "1 hr ago",
                    },
                ],
            },
            {
                "id": "RF-8261",
                "customer": "Alicia Romero",
                "customer_id": "CUS-75809",
                "amount": "£156.75",
                "amount_minor": 15675,
                "reason": "Subscription cancelled",
                "channel": "Card payment",
                "payment_method": "Mastercard ···· 3065",
                "age": "2 hr 43 min",
                "sla": "17 min remaining",
                "sla_state": "Due soon",
                "status": "Under review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "risk_flags": [],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "Refund request submitted",
                        "actor": "Customer support workflow",
                        "at": "2 hr 43 min ago",
                    },
                ],
            },
            {
                "id": "RF-8255",
                "customer": "Kofi Boateng",
                "customer_id": "CUS-75722",
                "amount": "£64.20",
                "amount_minor": 6420,
                "reason": "Duplicate cash withdrawal",
                "channel": "Cash withdrawal",
                "payment_method": "Debit card ···· 5502",
                "age": "3 hr 19 min",
                "sla": "Breached by 19 min",
                "sla_state": "Breached",
                "status": "Evidence requested",
                "assignee_id": "maya",
                "assignee": "Maya Patel",
                "risk_flags": ["Duplicate payment signal"],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "ATM settlement file requested",
                        "actor": "Maya Patel",
                        "at": "2 hr ago",
                    },
                ],
            },
            {
                "id": "RF-8249",
                "customer": "Ruby Evans",
                "customer_id": "CUS-75670",
                "amount": "£980.00",
                "amount_minor": 98000,
                "reason": "Goods not received",
                "channel": "Card payment",
                "payment_method": "Visa ···· 8814",
                "age": "3 hr 48 min",
                "sla": "Breached by 48 min",
                "sla_state": "Breached",
                "status": "Awaiting approval",
                "assignee_id": None,
                "assignee": "Unassigned",
                "risk_flags": ["Near approval threshold"],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "Merchant dispute resolved for customer",
                        "actor": "Disputes service",
                        "at": "43 min ago",
                    },
                ],
            },
            {
                "id": "RF-8241",
                "customer": "Omar Farouk",
                "customer_id": "CUS-75583",
                "amount": "£1,525.40",
                "amount_minor": 152540,
                "reason": "Transfer duplicated",
                "channel": "Bank transfer",
                "payment_method": "Account ···· 2038",
                "age": "4 hr 12 min",
                "sla": "Breached by 2 hr 12 min",
                "sla_state": "Breached",
                "status": "Awaiting second approval",
                "assignee_id": "priya",
                "assignee": "Priya Shah",
                "risk_flags": ["High value", "Duplicate payment signal"],
                "required_approvals": 2,
                "approval_count": 1,
                "approved_by": ["maya"],
                "audit": [
                    {
                        "action": "First approval recorded",
                        "actor": "Maya Patel",
                        "at": "1 hr ago",
                    },
                ],
            },
            {
                "id": "RF-8237",
                "customer": "Isla MacLeod",
                "customer_id": "CUS-75516",
                "amount": "£48.99",
                "amount_minor": 4899,
                "reason": "Card charged after cancellation",
                "channel": "Card payment",
                "payment_method": "Visa ···· 4461",
                "age": "5 hr 2 min",
                "sla": "Breached by 2 hr 2 min",
                "sla_state": "Breached",
                "status": "Under review",
                "assignee_id": None,
                "assignee": "Unassigned",
                "risk_flags": [],
                "required_approvals": 1,
                "approval_count": 0,
                "approved_by": [],
                "audit": [
                    {
                        "action": "Subscription cancellation verified",
                        "actor": "Billing service",
                        "at": "4 hr ago",
                    },
                ],
            },
            {
                "id": "RF-8230",
                "customer": "Mila Novak",
                "customer_id": "CUS-75449",
                "amount": "£214.30",
                "amount_minor": 21430,
                "reason": "Merchant dispute",
                "channel": "Card payment",
                "payment_method": "Mastercard ···· 9207",
                "age": "Yesterday",
                "sla": "Completed in 1 hr 18 min",
                "sla_state": "On track",
                "status": "Approved",
                "assignee_id": "maya",
                "assignee": "Maya Patel",
                "risk_flags": [],
                "required_approvals": 1,
                "approval_count": 1,
                "approved_by": ["maya"],
                "audit": [
                    {
                        "action": "Refund approved",
                        "actor": "Maya Patel",
                        "at": "Yesterday, 16:42",
                    },
                    {
                        "action": "Refund request submitted",
                        "actor": "Customer support workflow",
                        "at": "Yesterday, 15:24",
                    },
                ],
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

    def assign_refund(
        self,
        refund_id: str,
        assignee_id: str,
        assignee_name: str,
        reason: str,
    ) -> dict[str, object]:
        for refund in self.refunds:
            if refund["id"] != refund_id:
                continue
            refund["assignee_id"] = assignee_id
            refund["assignee"] = assignee_name
            if refund["status"] == "Awaiting approval":
                refund["status"] = "Under review"
            audit = refund["audit"]
            if not isinstance(audit, list):
                raise TypeError("Refund audit data is invalid")
            audit.insert(
                0,
                {
                    "action": f"Assigned to {assignee_name}: {reason}",
                    "actor": assignee_name,
                    "at": "Just now",
                },
            )
            return refund
        raise KeyError(refund_id)

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
            audit = refund["audit"]
            if not isinstance(audit, list):
                raise TypeError("Refund audit data is invalid")
            if len(approved_by) >= required_approvals:
                refund["status"] = "Approved"
                action = "Refund approved"
            else:
                refund["status"] = "Awaiting second approval"
                action = "First approval recorded"
            audit.insert(
                0,
                {
                    "action": f"{action}: {reason}",
                    "actor": approver_id,
                    "at": "Just now",
                },
            )
            return refund

        raise KeyError(refund_id)
