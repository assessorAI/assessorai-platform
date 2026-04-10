from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from assessorai.services.analytics import (
    calculate_risk_level,
)
from assessorai.services.analytics_helpers import get_funcionalidade_from_event


def _get_admin_token(client: TestClient) -> str:
    """Helper to get admin auth token"""
    # Register admin user first
    payload = {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "Admin",
        "lgpd_check": True,
        "role": "owner",
        "password": "admin123",
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
    
    # Now login
    response = client.post(
        "/auth/token",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def test_risk_level_calculation():
    """Test risk level logic"""
    assert calculate_risk_level(None) == "alto"  # Never logged in
    assert calculate_risk_level(5) == "ok"
    assert calculate_risk_level(10) == "baixo"
    assert calculate_risk_level(18) == "medio"
    assert calculate_risk_level(25) == "alto"


def test_funcionalidade_mapping():
    """Test event type to funcionalidade mapping"""
    assert get_funcionalidade_from_event("auth:login") == "auth"
    assert get_funcionalidade_from_event("expert_pl.analysis.success") == "expert_pl"
    assert get_funcionalidade_from_event("oficio.generate.success") == "oficios"
    assert get_funcionalidade_from_event("vector_search.query.success") == "vector_search"
    assert get_funcionalidade_from_event("unknown.event") == "outros"


def test_refresh_metrics_endpoint(client: TestClient, db_session):
    """Test metrics refresh endpoint"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.post("/admin/analytics/refresh", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "mandatos_updated" in data
    assert "users_updated" in data
    assert "reference_date" in data


def test_mandatos_summary(client: TestClient, db_session):
    """Test mandatos summary endpoint"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Refresh metrics first
    client.post("/admin/analytics/refresh", headers=headers)
    
    response = client.get("/admin/analytics/mandatos/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "total" in data
    assert "ativos" in data
    assert "inativos" in data
    assert "taxa_retencao" in data
    assert "por_cargo" in data
    assert "por_uf" in data
    assert "por_perfil" in data
    assert "por_espectro" in data
    assert "por_risco" in data


def test_funcionalidades_uso(client: TestClient, db_session):
    """Test funcionalidades breakdown"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/admin/analytics/funcionalidades?period=30d", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "total_logs" in data
    assert "funcionalidades" in data
    assert isinstance(data["funcionalidades"], list)


def test_engagement_mandatos(client: TestClient, db_session):
    """Test mandatos engagement list"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Refresh first
    client.post("/admin/analytics/refresh", headers=headers)
    
    response = client.get("/admin/analytics/engagement/mandatos", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "mandatos" in data
    assert "total" in data
    
    if len(data["mandatos"]) > 0:
        mandato = data["mandatos"][0]
        assert "status" in mandato
        assert "risk_level" in mandato
        assert "logs_7d" in mandato
        assert "logs_30d" in mandato


def test_mandatos_timeline(client: TestClient, db_session):
    """Test mandatos registration timeline"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/admin/analytics/mandatos/timeline?period=month", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "timeline" in data
    assert isinstance(data["timeline"], list)


def test_raw_audit_logs_json(client: TestClient, db_session):
    """Test raw audit logs endpoint with JSON format"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/admin/analytics/raw/audit-logs?format=json&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "total" in data
    assert "count" in data
    assert "logs" in data
    assert isinstance(data["logs"], list)
    
    if len(data["logs"]) > 0:
        log = data["logs"][0]
        assert "id" in log
        assert "event_type" in log
        assert "funcionalidade" in log


def test_raw_mandatos_json(client: TestClient, db_session):
    """Test raw mandatos endpoint with JSON format"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Refresh metrics first
    client.post("/admin/analytics/refresh", headers=headers)
    
    response = client.get("/admin/analytics/raw/mandatos?include_metrics=true&format=json", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "mandatos" in data
    assert "count" in data
    assert isinstance(data["mandatos"], list)
    
    if len(data["mandatos"]) > 0:
        mandato = data["mandatos"][0]
        assert "id" in mandato
        assert "nome_parlamentar" in mandato
        if "metrics" in mandato:
            assert "status" in mandato["metrics"]
            assert "risk_level" in mandato["metrics"]


def test_raw_users_json(client: TestClient, db_session):
    """Test raw users endpoint with JSON format"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Refresh metrics first
    client.post("/admin/analytics/refresh", headers=headers)
    
    response = client.get("/admin/analytics/raw/users?include_metrics=true&format=json", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "users" in data
    assert "count" in data
    assert isinstance(data["users"], list)
    
    if len(data["users"]) > 0:
        user = data["users"][0]
        assert "id" in user
        assert "email" in user
        assert "mandatos" in user


def test_raw_funcionalidades_detail(client: TestClient, db_session):
    """Test raw funcionalidades detail endpoint"""
    token = _get_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    response = client.get("/admin/analytics/raw/funcionalidades-detail?format=json", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "summary" in data
    assert "by_funcionalidade" in data
    assert "by_day" in data
    assert isinstance(data["by_funcionalidade"], list)


def test_analytics_unauthorized(client: TestClient):
    """Test that analytics requires admin auth"""
    response = client.get("/admin/analytics/mandatos/summary")
    assert response.status_code == 401


def test_login_creates_audit_log(client: TestClient, db_session):
    """Test that login creates an audit log entry"""
    # Register user first
    payload = {
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "Admin",
        "lgpd_check": True,
        "role": "owner",
        "password": "admin123",
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
    
    # Login
    response = client.post(
        "/auth/token",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Check that login was logged
    logs_response = client.get("/admin/analytics/raw/audit-logs?event_type=auth:login&limit=1", headers=headers)
    assert logs_response.status_code == 200
    logs_data = logs_response.json()
    
    # Should have at least the login we just made
    assert logs_data["total"] >= 1
    if logs_data["count"] > 0:
        log = logs_data["logs"][0]
        assert log["event_type"] == "auth:login"
        assert log["funcionalidade"] == "auth"
