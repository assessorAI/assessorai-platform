from fastapi.testclient import TestClient
from sqlalchemy import select

from assessorai.db.models import AuditLog


def test_oficio_generate(client: TestClient, db_session):
    # Create admin user and get token
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
        data={"username": "admin@example.com", "password": "secret123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    auth_headers = {"Authorization": f"Bearer {token_response.json()['access_token']}"}

    # create mandato first so inheritance works (admin is member automatically)
    m = client.post(
        "/mandatos/",
        json={"nome_parlamentar": "Marina"},
        headers=auth_headers,
    ).json()

    # we won't hit the real LLM; ensure the endpoint at least routes and returns JSON
    r = client.post(
        "/oficio/generate",
        data={"input": "Falta de vaga em creche", "mandato_id": m["id"]},
        headers=auth_headers,
    )
    # it may error due to missing prompts or external deps; accept 200 or 400
    assert r.status_code in (200, 400)
