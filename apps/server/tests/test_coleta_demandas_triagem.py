from typing import Any, Dict

from assessorai.db.models import ColetaDemandaTriagem as ColetaDemandaTriagemORM
from assessorai.db.models import Mandato as MandatoORM


class _FakeBlob:
    def __init__(self, name: str):
        self.name = name

    def upload_from_string(self, data: bytes, content_type: str):
        return None


class _FakeBucket:
    def blob(self, name: str) -> _FakeBlob:
        return _FakeBlob(name)


def _create_mandato(db_session) -> MandatoORM:
    mandato = MandatoORM(nome_parlamentar="Mandato Triagem")
    db_session.add(mandato)
    db_session.commit()
    db_session.refresh(mandato)
    return mandato


def test_extract_triagem_returns_structured_fields(client, db_session, monkeypatch):
    mandato = _create_mandato(db_session)
    expected = {
        "tipo": "reclamacao",
        "categoria": "infraestrutura",
        "descricao_processada": "Descricao limpa da demanda.",
        "local_texto": "Rua Principal, 123",
        "solicitante_nome": "Maria",
        "solicitante_email": "maria@example.com",
        "solicitante_telefone": "11999998888",
    }

    monkeypatch.setattr(
        "assessorai.routers.coleta_demandas_triagem.call_llm",
        lambda *args, **kwargs: expected,
    )

    response = client.post(
        "/coleta-demandas/triagem/extract",
        json={
            "mandato_id": mandato.id,
            "descricao_original": "Texto bruto",
            "local_texto": "Rua Principal, 123",
        },
    )
    assert response.status_code == 200
    assert response.json() == expected


def test_triagem_crud_flow(client, db_session):
    mandato = _create_mandato(db_session)

    create_payload: Dict[str, Any] = {
        "mandato_id": mandato.id,
        "descricao_original": "Buraco na rua principal.",
        "tipo": "reclamacao",
        "categoria": "infraestrutura",
        "descricao_processada": "Ha um buraco grande na rua principal.",
        "origem": "coleta_publica",
        "local_texto": "Rua Principal, 123",
        "solicitante_nome": "Joao",
        "solicitante_email": "joao@example.com",
        "solicitante_telefone": "11912345678",
    }

    create_response = client.post("/coleta-demandas/triagem", json=create_payload)
    assert create_response.status_code == 200
    created = create_response.json()
    triagem_id = created["id"]

    list_response = client.get(
        "/coleta-demandas/triagem",
        params={"mandato_id": mandato.id, "limit": 10, "offset": 0},
    )
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = client.get(
        f"/coleta-demandas/triagem/{triagem_id}",
        params={"mandato_id": mandato.id},
    )
    assert get_response.status_code == 200

    update_response = client.put(
        f"/coleta-demandas/triagem/{triagem_id}",
        params={"mandato_id": mandato.id},
        json={"tipo": "elogio", "descricao_processada": "Descricao atualizada."},
    )
    assert update_response.status_code == 200
    assert update_response.json()["tipo"] == "elogio"

    delete_response = client.delete(
        f"/coleta-demandas/triagem/{triagem_id}",
        params={"mandato_id": mandato.id},
    )
    assert delete_response.status_code == 200


def test_public_coleta_generates_triagem_record(client, db_session, monkeypatch):
    mandato = _create_mandato(db_session)
    monkeypatch.setenv("GCS_BUCKET_NAME", "test-bucket")
    monkeypatch.setattr("assessorai.routers.coleta_demandas._get_bucket", lambda: (_FakeBucket(), "test-bucket"))
    monkeypatch.setattr(
        "assessorai.routers.coleta_demandas_triagem.call_llm",
        lambda *args, **kwargs: {
            "tipo": "reclamacao",
            "categoria": "infraestrutura",
            "descricao_processada": "Descricao processada pela IA",
            "local_texto": "Rua Exemplo, 123",
            "solicitante_nome": "Maria da Silva",
            "solicitante_email": None,
            "solicitante_telefone": "11999999999",
        },
    )

    response = client.post(
        f"/coleta-demandas?mandato_id={mandato.id}",
        data={
            "descricao": "Buraco grande na rua principal perto da escola.",
            "endereco": "Rua Exemplo, 123",
            "nome_completo": "Maria da Silva",
            "telefone": "(11) 99999-9999",
            "bairro": "Centro",
            "data_nascimento": "01/12/1995",
        },
    )
    assert response.status_code == 200

    triagem = db_session.query(ColetaDemandaTriagemORM).filter_by(mandato_id=mandato.id).first()
    assert triagem is not None
    assert triagem.origem == "coleta_publica"
    assert triagem.coleta_demanda_id is not None
    assert triagem.tipo == "reclamacao"
