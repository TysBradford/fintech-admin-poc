from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    COMPLIANCE_ANALYST = "compliance_analyst"
    PRODUCT_MANAGER = "product_manager"
    SUPPORT_LEAD = "support_lead"


class Permission(str, Enum):
    KYC_READ = "kyc:read"
    KYC_WRITE = "kyc:write"
    FEATURE_FLAGS_READ = "feature_flags:read"
    FEATURE_FLAGS_WRITE = "feature_flags:write"
    REFUNDS_READ = "refunds:read"
    REFUNDS_WRITE = "refunds:write"
    USERS_READ = "users:read"
    USERS_WRITE = "users:write"


class User(BaseModel):
    id: str
    name: str
    email: str
    job_title: str
    department: str
    location: str
    last_active: str
    access_review: str
    mfa_status: str
    roles: list[Role]
    permissions: list[Permission] = Field(default_factory=list)
    avatar_color: str


class RoleUpdate(BaseModel):
    roles: list[Role] = Field(min_length=1)


class FeatureFlagUpdate(BaseModel):
    enabled: bool
    reason: str = Field(min_length=3, max_length=200)


class AssignmentRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=200)


class RefundRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=200)
