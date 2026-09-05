from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status

from app.models import Permission, Role, User

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
