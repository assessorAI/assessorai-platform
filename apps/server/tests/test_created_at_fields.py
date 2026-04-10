"""
Quick test to verify created_at fields are returned in API responses
"""
from fastapi.testclient import TestClient


def test_mandato_created_at_in_response(client: TestClient, db_session):
    """Verify created_at field is present in mandato response"""
    # Register admin user
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
                "nome_parlamentar": "Test Mandato",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "São Paulo",
                "ue": "SP",
            }
        ],
    }
    register_resp = client.post("/auth/register", json=payload)
    assert register_resp.status_code == 200
    
    # Login
    login_resp = client.post(
        "/auth/token",
        data={"username": "admin@example.com", "password": "admin123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List mandatos
    mandatos_resp = client.get("/mandatos/", headers=headers)
    assert mandatos_resp.status_code == 200
    data = mandatos_resp.json()
    
    assert "mandatos" in data
    assert len(data["mandatos"]) > 0
    
    mandato = data["mandatos"][0]
    print(f"\n✅ Mandato response keys: {mandato.keys()}")
    
    # Verify created_at is present
    assert "created_at" in mandato, f"created_at missing from mandato response. Keys: {mandato.keys()}"
    assert mandato["created_at"] is not None, "created_at is null"
    print(f"✅ Mandato created_at: {mandato['created_at']}")
    
    # Verify it's an ISO format datetime string
    from datetime import datetime
    parsed = datetime.fromisoformat(mandato["created_at"].replace("Z", "+00:00"))
    assert parsed is not None


def test_user_created_at_in_response(client: TestClient, db_session):
    """Verify created_at field is present in user response"""
    # Register user
    payload = {
        "email": "testuser@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "(11) 88888-8888",
        "permission_level": "Admin",
        "lgpd_check": True,
        "role": "staff",
        "password": "test123",
        "mandato": [],
    }
    register_resp = client.post("/auth/register", json=payload)
    assert register_resp.status_code == 200
    
    # Login
    login_resp = client.post(
        "/auth/token",
        data={"username": "testuser@example.com", "password": "test123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List users
    users_resp = client.get("/user/", headers=headers)
    assert users_resp.status_code == 200
    data = users_resp.json()
    
    assert "users" in data
    assert len(data["users"]) > 0
    
    user = data["users"][0]
    print(f"\n✅ User response keys: {user.keys()}")
    
    # Verify created_at is present
    assert "created_at" in user, f"created_at missing from user response. Keys: {user.keys()}"
    assert user["created_at"] is not None, "created_at is null"
    print(f"✅ User created_at: {user['created_at']}")
    
    # Verify it's an ISO format datetime string
    from datetime import datetime
    parsed = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    assert parsed is not None
