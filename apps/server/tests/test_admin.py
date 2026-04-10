from datetime import datetime, timedelta

from sqlalchemy import select


def _ensure_admin_headers(client):
    payload = {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "Admin",
        "lgpd_check": True,
        "role": "owner",
        "password": "secret123",
        "mandato": [
            {
                "nome_parlamentar": "Admin User",
                "casa_legislativa": "Assembleia Legislativa",
                "cargo_parlamentar": "Deputado Estadual",
                "municipio": "Belo Horizonte",
                "ue": "MG",
            }
        ],
    }
    client.post("/auth/register", json=payload)
    token_response = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_user(client, headers, email: str, permission_level: str = "User") -> None:
    payload = {
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": permission_level,
        "lgpd_check": True,
        "role": "tester",
        "password": "secret123",
        "mandato": [
            {
                "nome_parlamentar": "Test User",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "São Paulo",
                "ue": "SP",
            }
        ],
    }
    response = client.post("/user/", json=payload, headers=headers)
    assert response.status_code in (200, 400)


def test_admin_summary_requires_admin(client, manager_token):
    response = client.get("/admin/summary", headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == 403


def test_admin_summary_returns_metrics(client, db_session):
    from assessorai.db.models import User as UserORM

    headers = _ensure_admin_headers(client)
    _create_user(client, headers, "summary-user@example.com", permission_level="Manager")

    # Mark an existing user as inactive to exercise the inactive count.
    user = db_session.scalar(select(UserORM).where(UserORM.email == "summary-user@example.com"))
    user.is_active = False  # type: ignore[attr-defined]
    db_session.add(user)
    db_session.commit()

    response = client.get("/admin/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["users"]["total"] >= 1
    assert "by_permission" in data["users"]
    assert data["mandatos"]["total"] >= 1
    assert "pending_invitations" in data
    assert "tokens" in data


def test_admin_health_endpoint(client):
    headers = _ensure_admin_headers(client)
    response = client.get("/admin/health", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_status"] in {"ok", "warning", "error"}
    assert isinstance(payload["checks"], list)
    assert any(check["name"] == "database" for check in payload["checks"])


def test_admin_audit_endpoint(client):
    headers = _ensure_admin_headers(client)

    client.post(
        "/oficio/generate",
        data={"input": "Teste auditoria"},
        headers=headers,
    )

    response = client.get("/admin/audit/", headers=headers)
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert logs
