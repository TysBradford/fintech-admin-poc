from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from app.models import Permission, Role, User

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


def with_permissions(user: User) -> User:
    permissions: set[Permission] = set()
    for role in user.roles:
        permissions.update(ROLE_PERMISSIONS[role])
    return user.model_copy(update={"permissions": sorted(permissions, key=lambda item: item.value)})


def get_current_user(x_demo_user: str = Header(default="morgan")) -> User:
    user = DEMO_USERS.get(x_demo_user)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unknown demo identity",
        )
    return with_permissions(user)


def require_permission(permission: Permission) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}",
            )
        return user

    return dependency
