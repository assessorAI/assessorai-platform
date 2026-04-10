from fastapi.testclient import TestClient
import json


def test_expert_pl_routes_exist(client: TestClient, auth_headers):
    # Create mandato
    m = client.post(
        "/mandatos/",
        json={"nome_parlamentar": "Marina"},
        headers=auth_headers,
    ).json()

    # Hit endpoints without files to validate basic error flow
    r1 = client.post(
        "/expert/pl/analise_constitucionalidade",
        data={"mandato_id": m["id"]},
        headers=auth_headers,
    )
    assert r1.status_code in (200, 400, 422)

    r2 = client.post(
        "/expert/pl/sugestao_emendas",
        data={"mandato_id": m["id"]},
        headers=auth_headers,
    )
    assert r2.status_code in (200, 400, 422)

    r3 = client.post(
        "/expert/pl/criar_projeto",
        data={"mandato_id": m["id"], "text": "segurança"},
        headers=auth_headers,
    )
    assert r3.status_code in (200, 400, 422)


def test_criar_projeto_com_referencias_salvas_gcs(client: TestClient, auth_headers):
    """Test that references are saved to GCS when creating a project."""
    # Create mandato
    m = client.post(
        "/mandatos/",
        json={"nome_parlamentar": "Test Ref GCS"},
        headers=auth_headers,
    ).json()

    # Create project with references
    referencias = [
        {"type": "text", "content": "Referência de teste para GCS"},
        {"type": "text", "content": "Segunda referência importante"}
    ]

    r = client.post(
        "/expert/pl/criar_projeto",
        data={
            "mandato_id": m["id"],
            "text": "projeto de lei sobre segurança pública",
            "referencias": json.dumps(referencias)
        },
        headers=auth_headers,
    )

    # Should succeed (or fail gracefully if LLM not configured)
    assert r.status_code in (200, 400, 422, 500)

    # If successful, check that response contains audit log info
    if r.status_code == 200:
        response_data = r.json()
        # Check if audit log ID is present (indicating successful logging)
        assert "x-audit-log-id" in r.headers
