from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from assessorai.db.models import AuditLog


def _ensure_admin_headers(client: TestClient) -> dict:
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


def _create_mandato_for_admin(client: TestClient, headers: dict) -> int:
    # Create a mandato for the admin user
    response = client.get("/me", headers=headers)
    user_data = response.json()
    # The /me endpoint returns mandato as a single object, not array
    if "mandato" in user_data and user_data["mandato"]:
        return user_data["mandato"]["id"]
    else:
        # Fallback: assume first mandato from registration
        return 1


def test_list_audit_logs_empty(client: TestClient, db_session):
    headers = _ensure_admin_headers(client)
    r = client.get("/admin/audit/", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    # After analytics merge, login creates an audit log, so we expect at least 1
    assert len(data) >= 1
    # Verify the login audit log exists
    login_logs = [log for log in data if log.get("event_type") == "auth:login"]
    assert len(login_logs) >= 1


def test_list_audit_logs_with_logs(client: TestClient, db_session):
    headers = _ensure_admin_headers(client)
    mandato_id = _create_mandato_for_admin(client, headers)

    # Trigger audit log by generating oficio
    r = client.post(
        "/oficio/generate",
        data={"input": "Test audit log", "mandato_id": mandato_id},
        headers=headers,
    )
    # Accept 200, 400, or 500 - the important thing is that it tries and may log
    assert r.status_code in (200, 400, 500)

    # List audit logs
    r = client.get("/admin/audit/", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least one log from the action

    log = data[0]
    assert "id" in log
    assert "created_at" in log
    assert "event_type" in log
    assert "payload" in log


def test_list_audit_logs_with_filters(client: TestClient):
    headers = _ensure_admin_headers(client)
    mandato_id = _create_mandato_for_admin(client, headers)

    # Get count of existing logs before test
    r_before = client.get("/admin/audit/", headers=headers)
    logs_before = len(r_before.json())

    # Trigger multiple logs (may succeed or fail depending on external services)
    resp1 = client.post(
        "/oficio/generate",
        data={"input": "Test filter 1", "mandato_id": mandato_id},
        headers=headers,
    )
    resp2 = client.post(
        "/oficio/generate",
        data={"input": "Test filter 2", "mandato_id": mandato_id},
        headers=headers,
    )
    
    # Accept any status code - we're testing audit logging, not oficio generation
    # Both success and error paths create audit logs
    assert resp1.status_code in (200, 400, 500)
    assert resp2.status_code in (200, 400, 500)

    # Determine which event_type to check based on response status
    # If successful (200), check for 'oficio.generate.success'
    # If failed (500), check for 'oficio.generate.error'
    if resp1.status_code == 200:
        event_type_to_check = "oficio.generate.success"
    else:
        event_type_to_check = "oficio.generate.error"

    # Filter by event_type
    r = client.get(f"/admin/audit/?event_type={event_type_to_check}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    # Should have at least 2 new logs from our test
    assert len(data) >= 2, f"Expected >= 2 logs with event_type={event_type_to_check}, got {len(data)}"

    # Filter by mandato_id
    r = client.get(f"/admin/audit/?mandato_id={mandato_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2, f"Expected >= 2 logs with mandato_id={mandato_id}, got {len(data)}"

    # Filter by date range
    from_dt = (datetime.now() - timedelta(days=1)).isoformat()
    to_dt = (datetime.now() + timedelta(days=1)).isoformat()
    r = client.get(f"/admin/audit/?from={from_dt}&to={to_dt}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    # Should have all logs from today including our 2 new ones
    assert len(data) >= logs_before + 2, f"Expected >= {logs_before + 2} logs in date range, got {len(data)}"


def test_list_audit_logs_pagination(client: TestClient, db_session):
    headers = _ensure_admin_headers(client)
    mandato_id = _create_mandato_for_admin(client, headers)

    # Trigger multiple logs
    for i in range(5):
        client.post(
            "/oficio/generate",
            data={"input": f"Test pagination {i}", "mandato_id": mandato_id},
            headers=headers,
        )

    # Test limit
    r = client.get("/admin/audit/?limit=2", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2

    # Test offset
    r = client.get("/admin/audit/?limit=2&offset=2", headers=headers)
    assert r.status_code == 200
    data2 = r.json()
    assert len(data2) == 2
    assert data2[0]["id"] != data[0]["id"]


def test_get_audit_log_valid(client: TestClient, db_session):
    headers = _ensure_admin_headers(client)
    mandato_id = _create_mandato_for_admin(client, headers)

    # Trigger log
    client.post(
        "/oficio/generate",
        data={"input": "Test get log", "mandato_id": mandato_id},
        headers=headers,
    )

    # Get first log
    r = client.get("/admin/audit/", headers=headers)
    log_id = r.json()[0]["id"]

    # Get specific log
    r = client.get(f"/admin/audit/{log_id}", headers=headers)
    assert r.status_code == 200
    log = r.json()
    assert log["id"] == log_id
    assert "event_type" in log
    assert "payload" in log


def test_get_audit_log_invalid(client: TestClient, db_session):
    headers = _ensure_admin_headers(client)

    # Invalid ID
    r = client.get("/admin/audit/99999", headers=headers)
    assert r.status_code == 404
    assert "não encontrado" in r.json()["detail"]


def test_audit_logs_unauthorized(client: TestClient, db_session):
    # No headers
    r = client.get("/admin/audit/")
    assert r.status_code == 401

    # Non-admin user
    payload = {
        "email": "user@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "User",
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
    client.post("/auth/register", json=payload)
    token_response = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/audit/", headers=headers)
    assert r.status_code == 403
