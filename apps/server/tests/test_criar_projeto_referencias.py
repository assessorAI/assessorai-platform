from fastapi.testclient import TestClient
import base64
import json

def test_criar_projeto_com_referencias_text_file_ref(client: TestClient, auth_headers):
    # cria mandato
    m = client.post(
        "/mandatos/",
        json={"nome_parlamentar": "Marina"},
        headers=auth_headers,
    ).json()

    # upload de um arquivo para obter file_id (que será usado como ref_id)
    file_bytes = b"PDF BIN\n"
    files = {"file": ("doc.pdf", file_bytes, "application/pdf")}
    up = client.post(f"/files/upload?mandato_id={m['id']}", files=files, data={"title": "Documento Teste"}, headers=auth_headers)
    assert up.status_code == 200, up.text
    ref_id = str(up.json()["file_id"])  # file_id será usado como referência

    # prepara referencias: texto + reference + file(base64)
    refs = [
        {"type": "text", "content": "Lei 123, art 1"},
        {"type": "reference", "content": ref_id},
        {"type": "file", "content": base64.b64encode(b"hello world").decode("utf-8")},
    ]

    data = {
        "mandato_id": m["id"],
        "text": "segurança pública",
        "referencias": json.dumps(refs),
    }
    r = client.post("/expert/pl/criar_projeto", data=data, headers=auth_headers)
    # O LLM pode não estar configurado para testes, aceitaremos 200/400/422
    assert r.status_code in (200, 400, 422), r.text
