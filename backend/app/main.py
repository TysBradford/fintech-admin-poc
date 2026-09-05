from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.adapters import DemoFeatureFlagProvider, DemoKycDataSource, DemoPaymentsProvider
from app.auth import get_current_user, get_security_context, require_permission
from app.composition import build_security_context
from app.config import settings
from app.models import (
    AssignmentRequest,
    FeatureFlagUpdate,
    Permission,
    RefundRequest,
    RoleUpdate,
    User,
)
from app.ports import FeatureFlagProvider, KycDataSource, PaymentsProvider
from app.security import SecurityContext, UserNotFoundError

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
app.state.security = build_security_context(settings.auth_mode)

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
    security: SecurityContext = Depends(get_security_context),
    _: User = Depends(require_permission(Permission.USERS_READ)),
) -> list[User]:
    return security.authorization.list_users()


@app.put("/api/admin/users/{user_id}/roles", response_model=User)
def update_roles(
    user_id: str,
    payload: RoleUpdate,
    actor: User = Depends(require_permission(Permission.USERS_WRITE)),
    security: SecurityContext = Depends(get_security_context),
) -> User:
    try:
        return security.role_assignments.assign_roles(
            actor=actor,
            target_user_id=user_id,
            roles=payload.roles,
            reason=payload.reason,
        )
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from error


@app.get("/api/kyc/cases")
def list_kyc_cases(
    _: User = Depends(require_permission(Permission.KYC_READ)),
) -> list[dict[str, object]]:
    return kyc_source.list_cases()


@app.post("/api/kyc/cases/{case_id}/assign")
def assign_kyc_case(
    case_id: str,
    payload: AssignmentRequest,
    user: User = Depends(require_permission(Permission.KYC_WRITE)),
) -> dict[str, object]:
    try:
        return kyc_source.assign_case(case_id, user.id, user.name, payload.reason)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KYC case not found",
        ) from error


@app.get("/api/feature-flags")
def list_feature_flags(
    _: User = Depends(require_permission(Permission.FEATURE_FLAGS_READ)),
) -> list[dict[str, object]]:
    return flag_provider.list_flags()


@app.put("/api/feature-flags/{flag_id}")
def update_feature_flag(
    flag_id: str,
    payload: FeatureFlagUpdate,
    user: User = Depends(require_permission(Permission.FEATURE_FLAGS_WRITE)),
) -> dict[str, object]:
    try:
        return flag_provider.set_flag(flag_id, payload.enabled, user.name, payload.reason)
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


@app.post("/api/refunds/{refund_id}/assign")
def assign_refund(
    refund_id: str,
    payload: AssignmentRequest,
    user: User = Depends(require_permission(Permission.REFUNDS_WRITE)),
) -> dict[str, object]:
    try:
        return payments_provider.assign_refund(
            refund_id,
            user.id,
            user.name,
            payload.reason,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found",
        ) from error


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
