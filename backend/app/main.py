from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.adapters import DemoFeatureFlagProvider, DemoKycDataSource, DemoPaymentsProvider
from app.auth import DEMO_USERS, get_current_user, require_permission, with_permissions
from app.config import settings
from app.models import FeatureFlagUpdate, Permission, RefundRequest, RoleUpdate, User
from app.ports import FeatureFlagProvider, KycDataSource, PaymentsProvider

app = FastAPI(
    title="Fintech Admin API",
    version="0.1.0",
    description="Prototype API using synthetic data only.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

kyc_source: KycDataSource = DemoKycDataSource()
flag_provider: FeatureFlagProvider = DemoFeatureFlagProvider()
payments_provider: PaymentsProvider = DemoPaymentsProvider()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env, "auth_mode": settings.auth_mode}


@app.get("/api/auth/me", response_model=User)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@app.get("/api/admin/users", response_model=list[User])
def list_users(
    _: User = Depends(require_permission(Permission.USERS_READ)),
) -> list[User]:
    return [with_permissions(user) for user in DEMO_USERS.values()]


@app.put("/api/admin/users/{user_id}/roles", response_model=User)
def update_roles(
    user_id: str,
    payload: RoleUpdate,
    _: User = Depends(require_permission(Permission.USERS_WRITE)),
) -> User:
    user = DEMO_USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated_user = user.model_copy(update={"roles": payload.roles})
    DEMO_USERS[user_id] = updated_user
    return with_permissions(updated_user)


@app.get("/api/kyc/cases")
def list_kyc_cases(
    _: User = Depends(require_permission(Permission.KYC_READ)),
) -> list[dict[str, object]]:
    return kyc_source.list_cases()


@app.get("/api/feature-flags")
def list_feature_flags(
    _: User = Depends(require_permission(Permission.FEATURE_FLAGS_READ)),
) -> list[dict[str, object]]:
    return flag_provider.list_flags()


@app.put("/api/feature-flags/{flag_id}")
def update_feature_flag(
    flag_id: str,
    payload: FeatureFlagUpdate,
    _: User = Depends(require_permission(Permission.FEATURE_FLAGS_WRITE)),
) -> dict[str, object]:
    try:
        return flag_provider.set_flag(flag_id, payload.enabled)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature flag not found",
        ) from error


@app.get("/api/refunds")
def list_refunds(
    _: User = Depends(require_permission(Permission.REFUNDS_READ)),
) -> dict[str, object]:
    return {
        "summary": payments_provider.refund_summary(),
        "items": payments_provider.list_refunds(),
    }


@app.post("/api/refunds/{refund_id}/approve")
def approve_refund(
    refund_id: str,
    payload: RefundRequest,
    user: User = Depends(require_permission(Permission.REFUNDS_WRITE)),
) -> dict[str, object]:
    try:
        return payments_provider.approve_refund(refund_id, user.id, payload.reason)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found",
        ) from error
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
