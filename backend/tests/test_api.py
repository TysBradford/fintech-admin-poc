from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.adapters import DemoAuditSink
from app.composition import build_security_context
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_security_context() -> Iterator[None]:
    app.state.security = build_security_context("demo")
    yield


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["auth_mode"] == "demo"


def test_missing_demo_identity_is_rejected() -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_unknown_demo_identity_is_rejected() -> None:
    response = client.get("/api/auth/me", headers={"X-Demo-User": "unknown"})
    assert response.status_code == 401


def test_api_documents_bearer_authentication() -> None:
    security_schemes = app.openapi()["components"]["securitySchemes"]
    assert security_schemes["HTTPBearer"] == {
        "type": "http",
        "scheme": "bearer",
    }


@pytest.mark.parametrize(
    ("user_id", "path", "expected_status"),
    [
        ("amina", "/api/kyc/cases", 200),
        ("amina", "/api/feature-flags", 403),
        ("amina", "/api/refunds", 403),
        ("amina", "/api/admin/users", 403),
        ("leo", "/api/kyc/cases", 403),
        ("leo", "/api/feature-flags", 200),
        ("leo", "/api/refunds", 403),
        ("leo", "/api/admin/users", 403),
        ("priya", "/api/kyc/cases", 403),
        ("priya", "/api/feature-flags", 403),
        ("priya", "/api/refunds", 200),
        ("priya", "/api/admin/users", 403),
        ("morgan", "/api/kyc/cases", 200),
        ("morgan", "/api/feature-flags", 200),
        ("morgan", "/api/refunds", 200),
        ("morgan", "/api/admin/users", 200),
    ],
)
def test_role_permissions_guard_read_routes(
    user_id: str,
    path: str,
    expected_status: int,
) -> None:
    response = client.get(path, headers={"X-Demo-User": user_id})
    assert response.status_code == expected_status


def test_compliance_user_can_access_kyc() -> None:
    response = client.get("/api/kyc/cases", headers={"X-Demo-User": "amina"})
    assert response.status_code == 200
    assert response.json()[0]["id"] == "KYC-1048"


def test_compliance_user_cannot_access_feature_flags() -> None:
    response = client.get("/api/feature-flags", headers={"X-Demo-User": "amina"})
    assert response.status_code == 403


def test_super_admin_can_update_roles() -> None:
    response = client.put(
        "/api/admin/users/leo/roles",
        headers={"X-Demo-User": "morgan"},
        json={
            "roles": ["product_manager", "compliance_analyst"],
            "reason": "Temporary KYC review coverage",
        },
    )
    assert response.status_code == 200
    assert "kyc:read" in response.json()["permissions"]

    audit_sink = app.state.security.audit_sink
    assert isinstance(audit_sink, DemoAuditSink)
    event = audit_sink.events[-1]
    assert event.action == "roles.updated"
    assert event.actor_id == "morgan"
    assert event.target_id == "leo"
    assert event.reason == "Temporary KYC review coverage"
    assert [role.value for role in event.previous_roles] == ["product_manager"]
    assert [role.value for role in event.new_roles] == [
        "product_manager",
        "compliance_analyst",
    ]


def test_non_admin_cannot_update_roles() -> None:
    response = client.put(
        "/api/admin/users/leo/roles",
        headers={"X-Demo-User": "amina"},
        json={
            "roles": ["product_manager", "compliance_analyst"],
            "reason": "Attempted access change",
        },
    )
    assert response.status_code == 403


@pytest.mark.parametrize(
    ("user_id", "method", "path", "payload"),
    [
        (
            "amina",
            "PUT",
            "/api/feature-flags/refund-self-service",
            {"enabled": True, "reason": "Unauthorized flag change"},
        ),
        (
            "priya",
            "PUT",
            "/api/feature-flags/refund-self-service",
            {"enabled": True, "reason": "Unauthorized flag change"},
        ),
        (
            "amina",
            "POST",
            "/api/refunds/RF-8288/approve",
            {"reason": "Unauthorized refund approval"},
        ),
        (
            "leo",
            "POST",
            "/api/refunds/RF-8288/approve",
            {"reason": "Unauthorized refund approval"},
        ),
        (
            "leo",
            "PUT",
            "/api/admin/users/amina/roles",
            {"roles": ["compliance_analyst"], "reason": "Unauthorized role change"},
        ),
        (
            "priya",
            "PUT",
            "/api/admin/users/amina/roles",
            {"roles": ["compliance_analyst"], "reason": "Unauthorized role change"},
        ),
    ],
)
def test_role_permissions_guard_write_routes(
    user_id: str,
    method: str,
    path: str,
    payload: dict[str, object],
) -> None:
    response = client.request(
        method,
        path,
        headers={"X-Demo-User": user_id},
        json=payload,
    )
    assert response.status_code == 403


def test_product_manager_can_update_feature_flags() -> None:
    response = client.put(
        "/api/feature-flags/refund-self-service",
        headers={"X-Demo-User": "leo"},
        json={"enabled": True, "reason": "Approved staged rollout"},
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_role_update_requires_reason() -> None:
    response = client.put(
        "/api/admin/users/leo/roles",
        headers={"X-Demo-User": "morgan"},
        json={"roles": ["product_manager", "compliance_analyst"]},
    )
    assert response.status_code == 422


def test_role_update_rejects_blank_reason() -> None:
    response = client.put(
        "/api/admin/users/leo/roles",
        headers={"X-Demo-User": "morgan"},
        json={"roles": ["compliance_analyst"], "reason": "   "},
    )
    assert response.status_code == 422


def test_unconfigured_auth_mode_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="no configured identity provider"):
        build_security_context("entra")


def test_refund_approval_persists() -> None:
    response = client.post(
        "/api/refunds/RF-8283/approve",
        headers={"X-Demo-User": "morgan"},
        json={"reason": "Customer evidence verified"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Approved"

    refunds = client.get("/api/refunds", headers={"X-Demo-User": "morgan"})
    refund = next(item for item in refunds.json()["items"] if item["id"] == "RF-8283")
    assert refund["status"] == "Approved"


def test_high_value_refund_requires_distinct_second_approver() -> None:
    first_response = client.post(
        "/api/refunds/RF-8291/approve",
        headers={"X-Demo-User": "morgan"},
        json={"reason": "Transaction evidence verified"},
    )
    assert first_response.status_code == 200
    assert first_response.json()["status"] == "Awaiting second approval"

    duplicate_response = client.post(
        "/api/refunds/RF-8291/approve",
        headers={"X-Demo-User": "morgan"},
        json={"reason": "Second review attempt"},
    )
    assert duplicate_response.status_code == 409

    second_response = client.post(
        "/api/refunds/RF-8291/approve",
        headers={"X-Demo-User": "priya"},
        json={"reason": "Independent approval completed"},
    )
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "Approved"
