from app.adapters import (
    DemoAuditSink,
    DemoAuthorizationRepository,
    DemoAuthorizationUnitOfWorkFactory,
    DemoIdentityProvider,
)
from app.security import AuthorizationService, RoleAssignmentService, SecurityContext


def build_security_context(auth_mode: str) -> SecurityContext:
    if auth_mode != "demo":
        raise RuntimeError(f"AUTH_MODE={auth_mode!r} has no configured identity provider")

    repository = DemoAuthorizationRepository()
    audit_sink = DemoAuditSink()
    authorization = AuthorizationService(repository)
    unit_of_work_factory = DemoAuthorizationUnitOfWorkFactory(repository, audit_sink)
    return SecurityContext(
        identity_provider=DemoIdentityProvider(),
        authorization=authorization,
        role_assignments=RoleAssignmentService(authorization, unit_of_work_factory),
        audit_sink=audit_sink,
    )
