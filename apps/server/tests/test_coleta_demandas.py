from fastapi.testclient import TestClient


class _FakeBlob:
    def __init__(self, name: str):
        self.name = name
        self.payload = b""
        self.content_type = ""

    def upload_from_string(self, data: bytes, content_type: str):
        self.payload = data
        self.content_type = content_type


class _FakeBucket:
    def blob(self, name: str) -> _FakeBlob:
        return _FakeBlob(name)


def _create_mandato(client: TestClient) -> int:
    payload = {
        "email": "coleta-admin@example.com",
        "first_name": "Coleta",
        "last_name": "Admin",
        "phone": "(11) 99999-9999",
        "permission_level": "Admin",
        "lgpd_check": True,
        "role": "owner",
        "password": "secret123",
        "mandato": [
            {
                "nome_parlamentar": "Coleta",
                "casa_legislativa": "Camara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "Sao Paulo",
                "ue": "SP",
            }
        ],
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code in (200, 400)
    if response.status_code == 200:
        return response.json()["mandato"][0]["id"]

    token = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    return me.json()["mandato"][0]["id"]


def test_create_demanda_and_reuse_contact_token(client: TestClient, monkeypatch):
    mandato_id = _create_mandato(client)
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr("assessorai.routers.coleta_demandas._get_bucket", lambda: (_FakeBucket(), "test-bucket"))
    monkeypatch.setattr("assessorai.routers.coleta_demandas.persist_triagem_result", lambda **kwargs: None)

    response = client.post(
        f"/coleta-demandas?mandato_id={mandato_id}",
        data={
            "descricao": "Buraco grande na rua principal perto da escola.",
            "endereco": "Rua Exemplo, 123",
            "nome_completo": "Maria da Silva",
            "telefone": "(11) 99999-9999",
            "bairro": "Centro",
            "data_nascimento": "01/12/1995",
        },
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["message"] == "Demanda criada com sucesso"
    assert body["contact_token"]

    me_response = client.get("/coleta-demandas/me", params={"contact_token": body["contact_token"]})
    assert me_response.status_code == 200
    assert me_response.json()["user"]["nome_completo"] == "Maria da Silva"

    second = client.post(
        f"/coleta-demandas?mandato_id={mandato_id}",
        data={
            "descricao": "Falta de iluminacao em via publica no bairro.",
            "ponto_referencia": "Em frente ao mercado",
            "contact_token": body["contact_token"],
        },
    )
    assert second.status_code == 200, second.json()


def test_endereco_or_referencia_validation(client: TestClient, monkeypatch):
    mandato_id = _create_mandato(client)
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr("assessorai.routers.coleta_demandas._get_bucket", lambda: (_FakeBucket(), "test-bucket"))
    monkeypatch.setattr("assessorai.routers.coleta_demandas.persist_triagem_result", lambda **kwargs: None)

    missing_both = client.post(
        f"/coleta-demandas?mandato_id={mandato_id}",
        data={
            "descricao": "Descricao valida com mais de dez caracteres.",
            "nome_completo": "Jose Teste",
            "telefone": "11999999999",
            "bairro": "Centro",
            "data_nascimento": "10/10/1990",
        },
    )
    assert missing_both.status_code == 400

    invalid_date = client.post(
        f"/coleta-demandas?mandato_id={mandato_id}",
        data={
            "descricao": "Descricao valida com mais de dez caracteres.",
            "ponto_referencia": "Perto da praca",
            "nome_completo": "Jose Teste",
            "telefone": "11999999999",
            "bairro": "Centro",
            "data_nascimento": "1990-10-10",
        },
    )
    assert invalid_date.status_code == 422


def test_multiple_arquivos_supported(client: TestClient, monkeypatch):
    mandato_id = _create_mandato(client)
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr("assessorai.routers.coleta_demandas._get_bucket", lambda: (_FakeBucket(), "test-bucket"))
    monkeypatch.setattr("assessorai.routers.coleta_demandas.persist_triagem_result", lambda **kwargs: None)

    invalid_type = client.post(
        f"/coleta-demandas?mandato_id={mandato_id}",
        data={
            "descricao": "Descricao valida com mais de dez caracteres.",
            "ponto_referencia": "Perto da praca",
            "nome_completo": "Ana Teste",
            "telefone": "11999999999",
            "bairro": "Centro",
            "data_nascimento": "10/10/1990",
        },
        files=[("arquivos", ("a.txt", b"arquivo invalido", "text/plain"))],
    )
    assert invalid_type.status_code == 415

    valid = client.post(
        f"/coleta-demandas?mandato_id={mandato_id}",
        data={
            "descricao": "Descricao valida com mais de dez caracteres.",
            "ponto_referencia": "Perto da praca",
            "nome_completo": "Ana Teste",
            "telefone": "11999999999",
            "bairro": "Centro",
            "data_nascimento": "10/10/1990",
        },
        files=[
            ("arquivos", ("a.png", b"fakepng", "image/png")),
            ("arquivos", ("b.pdf", b"%PDF-1.4", "application/pdf")),
        ],
    )
    assert valid.status_code == 200, valid.json()
