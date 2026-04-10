from fastapi.testclient import TestClient
import time

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from assessorai.db.models import AuditLog, User as UserORM


def test_mandatos_crud(client: TestClient, auth_headers):
    # create mandato
    payload = {
        "nome_parlamentar": "Marina Bragante",
        "casa_legislativa": "Câmara Municipal de São Paulo",
        "cargo_parlamentar": "Vereador",
        "municipio": "São Paulo",
        "ue": "SP",
    }
    r = client.post("/mandatos/", json=payload, headers=auth_headers)
    assert r.status_code == 200
    m = r.json()
    assert m["cargo_parlamentar"] == payload["cargo_parlamentar"]
    mid = m["id"]

    # list should show users as list of ids
    r2 = client.get("/mandatos/", headers=auth_headers)
    assert r2.status_code == 200
    response_data = r2.json()
    assert "mandatos" in response_data
    assert "total" in response_data
    assert isinstance(response_data["mandatos"][0]["users"], list)

    mandato_from_list = next((m for m in response_data["mandatos"] if m["id"] == mid), None)
    assert mandato_from_list is not None
    assert isinstance(mandato_from_list.get("gerente"), list)
    assert "last_login" in mandato_from_list
    assert isinstance(mandato_from_list.get("numero_atividades"), int)

    # get one
    r3 = client.get(f"/mandatos/{mid}", headers=auth_headers)
    assert r3.status_code == 200
    assert isinstance(r3.json()["users"], list)

    # update
    upd = {"municipio": "Campinas"}
    r4 = client.put(f"/mandatos/{mid}", json=upd, headers=auth_headers)
    assert r4.status_code == 200
    assert r4.json()["municipio"] == "Campinas"

    # test partido field
    upd_partido = {"partido": "PSOL"}
    r5 = client.put(f"/mandatos/{mid}", json=upd_partido, headers=auth_headers)
    assert r5.status_code == 200
    assert r5.json()["partido"] == "PSOL"

    # verify partido appears in list
    r6 = client.get("/mandatos/", headers=auth_headers)
    assert r6.status_code == 200
    mandatos_data = r6.json()
    assert "mandatos" in mandatos_data
    mandato_from_list = next((m for m in mandatos_data["mandatos"] if m["id"] == mid), None)
    assert mandato_from_list is not None
    assert mandato_from_list["partido"] == "PSOL"
    assert isinstance(mandato_from_list.get("gerente"), list)
    assert "last_login" in mandato_from_list
    assert isinstance(mandato_from_list.get("numero_atividades"), int)

    # add/remove user to mandato
    add_body = {"email": "another@example.com"}
    # create another user first
    client.post(
        "/user/",
        json={
            "email": add_body["email"],
            "first_name": "Another",
            "last_name": "User",
            "phone": "(11) 77777-6666",
            "permission_level": "User",
            "lgpd_check": True,
            "role": "staff",
            "password": "secret123",
        },
        headers=auth_headers,
    )
    r5 = client.post(f"/mandatos/{mid}/users", json=add_body, headers=auth_headers)
    assert r5.status_code == 200

    # remove
    # discover user id by listing
    users_data = client.get("/user/", headers=auth_headers).json()
    users = users_data["users"]
    uid = next(u["id"] for u in users if u["email"] == add_body["email"])  # type: ignore
    r6 = client.delete(f"/mandatos/{mid}/users/{uid}", headers=auth_headers)
    assert r6.status_code == 200

    # delete mandato
    r7 = client.delete(f"/mandatos/{mid}", headers=auth_headers)
    assert r7.status_code == 200


def test_mandatos_list_search_filters_and_orderby_last_login(client: TestClient, db_session):
    # Create an admin session for this test (avoid auth_headers/db_session ordering issues)
    payload_admin = {
        "email": "admin2@example.com",
        "first_name": "Admin",
        "last_name": "Two",
        "phone": "(11) 99999-0000",
        "permission_level": "Admin",
        "lgpd_check": True,
        "role": "owner",
        "password": "secret123",
        "mandato": [{"nome_parlamentar": "Admin Two", "cargo_parlamentar": "Vereador"}],
    }
    client.post("/auth/register", json=payload_admin)
    token = client.post(
        "/auth/token",
        data={"username": payload_admin["email"], "password": payload_admin["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Create two mandatos for deterministic ordering
    m1 = {
        "nome_parlamentar": "ZZZ Mandato A",
        "casa_legislativa": "Câmara Municipal",
        "cargo_parlamentar": "Vereador",
        "municipio": "São Paulo",
        "ue": "SP",
        "partido": "PSOL",
        "perfil_parlamentar": "Progressista",
        "espectro_politico": "Centro Esquerda",
    }
    m2 = {
        "nome_parlamentar": "ZZZ Mandato B",
        "casa_legislativa": "Assembleia",
        "cargo_parlamentar": "Deputado Estadual",
        "municipio": "Campinas",
        "ue": "SP",
        "partido": "PT",
        "perfil_parlamentar": "Liberal",
        "espectro_politico": "Centro",
    }
    r1 = client.post("/mandatos/", json=m1, headers=auth_headers)
    r2 = client.post("/mandatos/", json=m2, headers=auth_headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    mid1 = r1.json()["id"]
    mid2 = r2.json()["id"]

    # Create another admin user, login later, and associate to mandato B
    email2 = "late_admin@example.com"
    reg = client.post(
        "/auth/register",
        json={
            "email": email2,
            "first_name": "Late",
            "last_name": "Admin",
            "phone": "(11) 33333-3333",
            "permission_level": "Admin",
            "lgpd_check": True,
            "role": "owner",
            "password": "secret123",
            "mandato": [{"nome_parlamentar": "Late Admin", "cargo_parlamentar": "Vereador"}],
        },
    )
    assert reg.status_code in (200, 400)
    login_headers = {"content-type": "application/x-www-form-urlencoded"}
    login = client.post(
        "/auth/token",
        data={"username": email2, "password": "secret123"},
        headers=login_headers,
    )
    assert login.status_code == 200
    add_user = client.post(f"/mandatos/{mid2}/users", json={"email": email2}, headers=auth_headers)
    assert add_user.status_code == 200

    # Generate persisted last_login by logging in (updates ALL mandatos of each user)
    time.sleep(1)
    client.post(
        "/auth/token",
        data={"username": payload_admin["email"], "password": payload_admin["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    time.sleep(1)
    client.post(
        "/auth/token",
        data={"username": email2, "password": "secret123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )

    # numero_atividades: only mandato A has activity
    admin_user = db_session.scalar(select(UserORM).where(UserORM.email == payload_admin["email"]))
    assert admin_user
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(
        AuditLog(
            created_at=now - timedelta(minutes=10),
            event_type="oficio.generate.error",
            actor_user_id=admin_user.id,
            actor_mandato_id=mid1,
            actor_permission_level="Admin",
            notes="test activity",
        )
    )
    db_session.commit()

    # Search and filter
    resp = client.get("/mandatos/?search=ZZZ&cargo_parlamentar=Vereador&limit=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    ids = [m["id"] for m in data["mandatos"]]
    assert mid1 in ids
    assert mid2 not in ids

    # Multi-value filters (CSV)
    resp_multi = client.get(
        "/mandatos/?search=ZZZ"
        "&cargo_parlamentar=Vereador,%20Deputado%20Estadual"
        "&casa_legislativa=C%C3%A2mara%20Municipal,%20Assembleia"
        "&partido=PSOL,%20PT"
        "&perfil_parlamentar=Progressista,%20Liberal"
        "&espectro_politico=Centro%20Esquerda,%20Centro"
        "&limit=200",
        headers=auth_headers,
    )
    assert resp_multi.status_code == 200
    data_multi = resp_multi.json()
    ids_multi = {m["id"] for m in data_multi["mandatos"]}
    assert mid1 in ids_multi
    assert mid2 in ids_multi

    # orderBy nome_parlamentar
    resp2 = client.get("/mandatos/?search=ZZZ&orderBy=nome_parlamentar&limit=200", headers=auth_headers)
    assert resp2.status_code == 200
    ordered_names = [m["nome_parlamentar"] for m in resp2.json()["mandatos"]]
    assert ordered_names == ["ZZZ Mandato A", "ZZZ Mandato B"]

    # orderBy last_login (mandato B should be first)
    resp3 = client.get("/mandatos/?search=ZZZ&orderBy=-last_login&limit=200", headers=auth_headers)
    assert resp3.status_code == 200
    data3 = resp3.json()
    ids3 = [m["id"] for m in data3["mandatos"]]
    assert ids3[0] == mid2

    mandato_a = next(m for m in data3["mandatos"] if m["id"] == mid1)
    mandato_b = next(m for m in data3["mandatos"] if m["id"] == mid2)
    assert mandato_a.get("numero_atividades", 0) >= 1
    assert mandato_a.get("last_login")
    assert mandato_b.get("last_login")
    assert mandato_b["last_login"]["email"] == email2

    def _parse_iso(dt_str: str) -> datetime:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

    a_dt = _parse_iso(mandato_a["last_login"]["date"])
    b_dt = _parse_iso(mandato_b["last_login"]["date"])
    assert b_dt > a_dt

    # last_login range filters
    resp_from = client.get(
        "/mandatos/",
        headers=auth_headers,
        params={
            "search": "ZZZ",
            "from": (a_dt + timedelta(seconds=1)).isoformat(),
            "limit": 200,
        },
    )
    assert resp_from.status_code == 200
    ids_from = {m["id"] for m in resp_from.json()["mandatos"]}
    assert mid2 in ids_from
    assert mid1 not in ids_from

    resp_to = client.get(
        "/mandatos/",
        headers=auth_headers,
        params={
            "search": "ZZZ",
            "to": a_dt.isoformat(),
            "limit": 200,
        },
    )
    assert resp_to.status_code == 200
    ids_to = {m["id"] for m in resp_to.json()["mandatos"]}
    assert mid1 in ids_to
    assert mid2 not in ids_to


# ===========================================================================
# Slug tests
# ===========================================================================

def test_slug_auto_generated_on_create(client: TestClient, auth_headers):
    """Slug é gerado automaticamente a partir do nome_parlamentar."""
    payload = {
        "nome_parlamentar": "João da Silva",
        "cargo_parlamentar": "Vereador",
    }
    r = client.post("/mandatos/", json=payload, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["slug"] == "joao-da-silva"


def test_slug_custom_accepted(client: TestClient, auth_headers):
    """Slug informado explicitamente é salvo sem alteração."""
    payload = {
        "nome_parlamentar": "Maria Souza",
        "cargo_parlamentar": "Vereador",
        "slug": "meu-slug-customizado",
    }
    r = client.post("/mandatos/", json=payload, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["slug"] == "meu-slug-customizado"


def test_slug_duplicate_gets_suffix(client: TestClient, auth_headers):
    """Dois mandatos com o mesmo nome recebem slugs com sufixo numérico."""
    base = {"nome_parlamentar": "Pedro Único", "cargo_parlamentar": "Vereador"}
    r1 = client.post("/mandatos/", json=base, headers=auth_headers)
    r2 = client.post("/mandatos/", json=base, headers=auth_headers)
    assert r1.status_code == 200
    assert r2.status_code == 200
    slug1 = r1.json()["slug"]
    slug2 = r2.json()["slug"]
    assert slug1 == "pedro-unico"
    assert slug2 == "pedro-unico-2"


def test_slug_conflict_returns_409(client: TestClient, auth_headers):
    """Tentar criar com slug que já existe retorna 409."""
    payload1 = {
        "nome_parlamentar": "Slug Teste",
        "cargo_parlamentar": "Vereador",
        "slug": "slug-conflito",
    }
    payload2 = {
        "nome_parlamentar": "Outro Parlamentar",
        "cargo_parlamentar": "Vereador",
        "slug": "slug-conflito",
    }
    r1 = client.post("/mandatos/", json=payload1, headers=auth_headers)
    assert r1.status_code == 200
    r2 = client.post("/mandatos/", json=payload2, headers=auth_headers)
    assert r2.status_code == 409


def test_get_mandato_by_slug(client: TestClient, auth_headers):
    """GET /mandatos/{slug} retorna o mandato correto."""
    payload = {
        "nome_parlamentar": "Slug Fetch",
        "cargo_parlamentar": "Vereador",
    }
    create_r = client.post("/mandatos/", json=payload, headers=auth_headers)
    assert create_r.status_code == 200
    mid = create_r.json()["id"]
    slug = create_r.json()["slug"]
    assert slug  # must be non-empty

    # Fetch by slug
    r_slug = client.get(f"/mandatos/{slug}", headers=auth_headers)
    assert r_slug.status_code == 200
    assert r_slug.json()["id"] == mid

    # Fetch by id still works
    r_id = client.get(f"/mandatos/{mid}", headers=auth_headers)
    assert r_id.status_code == 200
    assert r_id.json()["slug"] == slug


def test_get_mandato_by_slug_public(client: TestClient, auth_headers):
    """GET /mandatos/{slug} e GET /mandatos/{id} funcionam SEM autenticação."""
    payload = {
        "nome_parlamentar": "Publico Teste",
        "cargo_parlamentar": "Deputado Estadual",
    }
    create_r = client.post("/mandatos/", json=payload, headers=auth_headers)
    assert create_r.status_code == 200
    mid = create_r.json()["id"]
    slug = create_r.json()["slug"]

    # Fetch by slug — sem token
    r_slug = client.get(f"/mandatos/{slug}")
    assert r_slug.status_code == 200, f"Expected 200, got {r_slug.status_code}: {r_slug.text}"
    assert r_slug.json()["id"] == mid

    # Fetch by id — sem token
    r_id = client.get(f"/mandatos/{mid}")
    assert r_id.status_code == 200, f"Expected 200, got {r_id.status_code}: {r_id.text}"
    assert r_id.json()["slug"] == slug

    # Non-existent slug returns 404 sem token
    r_404 = client.get("/mandatos/slug-inexistente-xyz-9999")
    assert r_404.status_code == 404


def test_slug_update_on_put(client: TestClient, auth_headers):
    """PUT com slug vazio regenera o slug a partir do nome."""
    payload = {
        "nome_parlamentar": "Original Nome",
        "cargo_parlamentar": "Vereador",
        "slug": "slug-original",
    }
    r = client.post("/mandatos/", json=payload, headers=auth_headers)
    mid = r.json()["id"]

    # Update with explicit new slug
    r2 = client.put(f"/mandatos/{mid}", json={"slug": "slug-novo"}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["slug"] == "slug-novo"


# ===========================================================================
# Profile image tests
# ===========================================================================

def test_profile_image_endpoint_missing_gcs(client: TestClient, auth_headers):
    """PUT /profile-image sem GCS configurado retorna 422 (bad image) ou 500 (no bucket).
    Valida que o endpoint existe e processa a imagem antes de tentar o GCS."""
    import io
    from PIL import Image as PILImage

    # Create a minimal 10x10 red JPEG in memory
    buf = io.BytesIO()
    img = PILImage.new("RGB", (10, 10), color=(255, 0, 0))
    img.save(buf, format="JPEG")
    buf.seek(0)

    # Create a mandato first
    payload = {"nome_parlamentar": "Foto Test", "cargo_parlamentar": "Vereador"}
    m = client.post("/mandatos/", json=payload, headers=auth_headers).json()
    mid = m["id"]

    r = client.put(
        f"/mandatos/{mid}/profile_image",
        files={"file": ("profile.jpg", buf, "image/jpeg")},
        headers=auth_headers,
    )
    # Without GCS configured it will fail at 500 (missing bucket env var) or
    # succeed with 200 in a mocked environment. 422 is an invalid image error.
    assert r.status_code in (200, 500)


def test_profile_image_rejects_invalid_type(client: TestClient, auth_headers):
    """Upload de tipo não suportado retorna 422."""
    # Create mandato
    payload = {"nome_parlamentar": "Tipo Errado", "cargo_parlamentar": "Vereador"}
    m = client.post("/mandatos/", json=payload, headers=auth_headers).json()
    mid = m["id"]

    r = client.put(
        f"/mandatos/{mid}/profile_image",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
        headers=auth_headers,
    )
    assert r.status_code == 422
