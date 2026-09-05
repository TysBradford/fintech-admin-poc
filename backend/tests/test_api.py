from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["auth_mode"] == "demo"


def test_compliance_user_can_access_kyc() -> None:
    response = client.get("/api/kyc/cases", headers={"X-Demo-User": "amina"})
    assert response.status_code == 200
    assert response.json()[0]["id"] == "KYC-1048"


def test_open_access_grants_every_user_all_permissions() -> None:
    response = client.get("/api/feature-flags", headers={"X-Demo-User": "amina"})
    assert response.status_code == 200

    me = client.get("/api/auth/me", headers={"X-Demo-User": "amina"})
    assert "users:write" in me.json()["permissions"]


def test_super_admin_can_update_roles() -> None:
    response = client.put(
        "/api/admin/users/leo/roles",
        headers={"X-Demo-User": "morgan"},
        json={"roles": ["product_manager", "compliance_analyst"]},
    )
    assert response.status_code == 200
    assert "kyc:read" in response.json()["permissions"]


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
