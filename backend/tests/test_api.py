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


def test_compliance_user_cannot_access_feature_flags() -> None:
    response = client.get("/api/feature-flags", headers={"X-Demo-User": "amina"})
    assert response.status_code == 403


def test_super_admin_can_update_roles() -> None:
    response = client.put(
        "/api/admin/users/leo/roles",
        headers={"X-Demo-User": "morgan"},
        json={"roles": ["product_manager", "compliance_analyst"]},
    )
    assert response.status_code == 200
    assert "kyc:read" in response.json()["permissions"]
