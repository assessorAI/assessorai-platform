from typing import Dict


def _register_user(client, *, email: str, mandato: Dict[str, str]) -> None:
    payload = {
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "member",
        "password": "secret123",
        "mandato": [mandato],
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 200, response.json()


def test_validate_email_endpoint(client):
    email = "unique_validation@example.com"
    not_exists_response = client.get("/validation/email", params={"email": email})
    assert not_exists_response.status_code == 200
    assert not_exists_response.json() == {"exists": False}

    mandato_data = {
        "nome_parlamentar": "Validar Email",
        "casa_legislativa": "Câmara Municipal A",
        "cargo_parlamentar": "Vereador",
        "municipio": "Cidade A",
        "ue": "SP",
    }
    _register_user(client, email=email, mandato=mandato_data)

    exists_response = client.get("/validation/email", params={"email": email})
    assert exists_response.status_code == 200
    assert exists_response.json() == {"exists": True}


def test_validate_slug_endpoint(client, auth_headers):
    slug = "slug-validation-check"
    not_exists_response = client.get("/validation/slug", params={"slug": slug})
    assert not_exists_response.status_code == 200
    assert not_exists_response.json() == {"exists": False}

    create_response = client.post(
        "/mandatos/",
        json={
            "nome_parlamentar": "Slug Validation Check",
            "cargo_parlamentar": "Vereador",
            "slug": slug,
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200, create_response.json()

    exists_response = client.get("/validation/slug", params={"slug": f"  {slug}  "})
    assert exists_response.status_code == 200
    assert exists_response.json() == {"exists": True}


def test_validate_mandato_endpoint(client):
    mandato_payload = {
        "nome_parlamentar": "Patrícia Souza",
        "casa_legislativa": "Assembleia Legislativa B",
        "cargo_parlamentar": "Deputado Estadual",
        "municipio": "Cidade B",
        "ue": "RJ",
        "perfil_parlamentar": "Partido Verde",
    }
    _register_user(client, email="mandato_validation@example.com", mandato=mandato_payload)

    # Should detect existing mandate using provided fields
    request_payload = {
        "nome": "Patrícia Souza",
        "casa_legislativa": "Assembleia Legislativa B",
        "partido": "Partido Verde",
        "cidade": "Cidade B",
        "uf": "RJ",
    }
    exists_response = client.post("/validation/mandato", json=request_payload)
    assert exists_response.status_code == 200
    assert exists_response.json() == {"exists": True}

    # Changing one field should return False
    missing_response = client.post(
        "/validation/mandato",
        json={**request_payload, "cidade": "Outra Cidade"},
    )
    assert missing_response.status_code == 200
    assert missing_response.json() == {"exists": False}
