"""
Tests for prompt evaluation system
"""
import io
import pytest
from fastapi.testclient import TestClient


def _get_or_create_mandato(client: TestClient, auth_headers: dict) -> int:
    """Helper to get or create a mandato for testing"""
    # Try to get existing mandatos
    response = client.get("/mandatos?limit=1", headers=auth_headers)
    if response.status_code == 200:
        data = response.json()
        mandatos = data.get("mandatos", [])
        if mandatos and len(mandatos) > 0:
            return mandatos[0]["id"]
    
    # Create a mandato if none exist
    mandato_data = {
        "nome_parlamentar": "Test Parliamentar",
        "casa_legislativa": "Câmara Municipal",
        "cargo_parlamentar": "Vereador",
        "municipio": "São Paulo",
        "ue": "SP"
    }
    response = client.post("/mandatos", json=mandato_data, headers=auth_headers)
    if response.status_code == 201:
        return response.json()["id"]
    
    # Fallback - use ID 1 (should exist from fixtures)
    return 1


def test_create_evaluation_case(client: TestClient, auth_headers: dict):
    """Test creating an evaluation test case"""
    case_data = {
        "name": "Test Ofício Case",
        "test_type": "oficio",
        "input_data": {
            "input": "Solicitar informações sobre processo administrativo",
            "orgao_destino": "Secretaria de Finanças",
            "remetente": "Vereador Teste",
            "data": "01 de janeiro de 2025",
            "mandato": {
                "nome_parlamentar": "Vereador Teste",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "perfil_parlamentar": "Fiscalizador",
                "espectro_politico": "Centro",
                "temas_interesse": "Transparência"
            }
        },
        "expected_output": "Ofício formal solicitando informações"
    }
    
    response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == case_data["name"]
    assert data["test_type"] == case_data["test_type"]
    assert data["is_active"] is True
    assert "id" in data


def test_create_evaluation_case_invalid_type(client: TestClient, auth_headers: dict):
    """Test creating a case with invalid test_type"""
    case_data = {
        "name": "Invalid Case",
        "test_type": "invalid_type",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Invalid test_type" in response.json()["detail"]


def test_list_evaluation_cases(client: TestClient, auth_headers: dict):
    """Test listing evaluation cases"""
    # Create a case first
    case_data = {
        "name": "List Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    
    # List cases
    response = client.get(
        "/admin/prompt-evaluation/cases",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_evaluation_case(client: TestClient, auth_headers: dict):
    """Test getting a specific evaluation case"""
    # Create a case first
    case_data = {
        "name": "Get Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    # Get the case
    response = client.get(
        f"/admin/prompt-evaluation/cases/{case_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["name"] == case_data["name"]


def test_update_evaluation_case(client: TestClient, auth_headers: dict):
    """Test updating an evaluation case"""
    # Create a case first
    case_data = {
        "name": "Update Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    # Update the case
    update_data = {
        "name": "Updated Test Case",
        "expected_output": "updated output"
    }
    
    response = client.patch(
        f"/admin/prompt-evaluation/cases/{case_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["expected_output"] == update_data["expected_output"]


def test_delete_evaluation_case_soft(client: TestClient, auth_headers: dict):
    """Test soft deleting an evaluation case"""
    # Create a case first
    case_data = {
        "name": "Delete Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    # Soft delete the case
    response = client.delete(
        f"/admin/prompt-evaluation/cases/{case_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify it's not in active list
    list_response = client.get(
        "/admin/prompt-evaluation/cases?is_active=true",
        headers=auth_headers
    )
    cases = list_response.json()
    case_ids = [c["id"] for c in cases]
    assert case_id not in case_ids


def test_export_cases_csv(client: TestClient, auth_headers: dict):
    """Test exporting cases to CSV"""
    # Create a case first
    case_data = {
        "name": "Export Test Case",
        "test_type": "oficio",
        "input_data": {
            "input": "test input",
            "orgao_destino": "Test Org",
            "remetente": "Test Sender"
        },
        "expected_output": "test output"
    }
    
    client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    
    # Export CSV
    response = client.get(
        "/admin/prompt-evaluation/cases/export-csv",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "evaluation_cases_" in response.headers["content-disposition"]
    
    # Check CSV content
    csv_content = response.text
    assert "name,test_type,input_text" in csv_content
    assert "Export Test Case" in csv_content


def test_create_evaluation_run(client: TestClient, auth_headers: dict):
    """Test creating an evaluation run"""
    # Get a valid mandato
    mandato_id = _get_or_create_mandato(client, auth_headers)
    
    # Create a case first
    case_data = {
        "name": "Run Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    # Create run with required fields
    run_data = {
        "run_name": "Test Run",
        "case_ids": [case_id],
        "mandato_ids": [mandato_id],
        "template_ids": [None]  # None = use default template
    }
    
    response = client.post(
        "/admin/prompt-evaluation/runs",
        json=run_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["run_name"] == run_data["run_name"]
    assert data["total_cases"] == 1
    assert data["status"] == "pending"
    assert "id" in data


def test_create_evaluation_run_invalid_cases(client: TestClient, auth_headers: dict):
    """Test creating a run with invalid case IDs"""
    mandato_id = _get_or_create_mandato(client, auth_headers)
    
    run_data = {
        "run_name": "Invalid Run",
        "case_ids": [99999],  # Non-existent ID
        "mandato_ids": [mandato_id],
        "template_ids": [None]
    }
    
    response = client.post(
        "/admin/prompt-evaluation/runs",
        json=run_data,
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "invalid or inactive" in response.json()["detail"].lower()


def test_list_evaluation_runs(client: TestClient, auth_headers: dict):
    """Test listing evaluation runs"""
    mandato_id = _get_or_create_mandato(client, auth_headers)
    
    # Create a case and run first
    case_data = {
        "name": "List Run Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    run_data = {
        "run_name": "List Test Run",
        "case_ids": [case_id],
        "mandato_ids": [mandato_id],
        "template_ids": [None]
    }
    
    client.post(
        "/admin/prompt-evaluation/runs",
        json=run_data,
        headers=auth_headers
    )
    
    # List runs
    response = client.get(
        "/admin/prompt-evaluation/runs",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_evaluation_run(client: TestClient, auth_headers: dict):
    """Test getting a specific evaluation run"""
    mandato_id = _get_or_create_mandato(client, auth_headers)
    
    # Create a case and run first
    case_data = {
        "name": "Get Run Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    run_data = {
        "run_name": "Get Test Run",
        "case_ids": [case_id],
        "mandato_ids": [mandato_id],
        "template_ids": [None]
    }
    
    run_response = client.post(
        "/admin/prompt-evaluation/runs",
        json=run_data,
        headers=auth_headers
    )
    run_id = run_response.json()["id"]
    
    # Get the run
    response = client.get(
        f"/admin/prompt-evaluation/runs/{run_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == run_id
    assert data["run_name"] == run_data["run_name"]


def test_list_evaluation_results(client: TestClient, auth_headers: dict):
    """Test listing evaluation results"""
    mandato_id = _get_or_create_mandato(client, auth_headers)
    
    # Create a case and run first
    case_data = {
        "name": "Results Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    run_data = {
        "run_name": "Results Test Run",
        "case_ids": [case_id],
        "mandato_ids": [mandato_id],
        "template_ids": [None]
    }
    
    run_response = client.post(
        "/admin/prompt-evaluation/runs",
        json=run_data,
        headers=auth_headers
    )
    run_id = run_response.json()["id"]
    
    # List results
    response = client.get(
        f"/admin/prompt-evaluation/results?run_id={run_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have one placeholder result
    assert len(data) == 1
    assert data[0]["run_id"] == run_id
    assert data[0]["case_id"] == case_id


def test_update_evaluation_result(client: TestClient, auth_headers: dict):
    """Test updating an evaluation result with human evaluation"""
    mandato_id = _get_or_create_mandato(client, auth_headers)
    
    # Create a case and run first
    case_data = {
        "name": "Update Result Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    run_data = {
        "run_name": "Update Result Test Run",
        "case_ids": [case_id],
        "mandato_ids": [mandato_id],
        "template_ids": [None]
    }
    
    run_response = client.post(
        "/admin/prompt-evaluation/runs",
        json=run_data,
        headers=auth_headers
    )
    run_id = run_response.json()["id"]
    
    # Get result ID
    results_response = client.get(
        f"/admin/prompt-evaluation/results?run_id={run_id}",
        headers=auth_headers
    )
    result_id = results_response.json()[0]["id"]
    
    # Update result with human evaluation
    update_data = {
        "human_evaluation": "Good output. Score: 90/100"
    }
    
    response = client.patch(
        f"/admin/prompt-evaluation/results/{result_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["human_evaluation"] == update_data["human_evaluation"]


def test_export_results_csv(client: TestClient, auth_headers: dict):
    """Test exporting results to CSV"""
    mandato_id = _get_or_create_mandato(client, auth_headers)
    
    # Create a case and run first
    case_data = {
        "name": "Export Results Test Case",
        "test_type": "oficio",
        "input_data": {"input": "test"},
        "expected_output": "test"
    }
    
    create_response = client.post(
        "/admin/prompt-evaluation/cases",
        json=case_data,
        headers=auth_headers
    )
    case_id = create_response.json()["id"]
    
    run_data = {
        "run_name": "Export Results Test Run",
        "case_ids": [case_id],
        "mandato_ids": [mandato_id],
        "template_ids": [None]
    }
    
    run_response = client.post(
        "/admin/prompt-evaluation/runs",
        json=run_data,
        headers=auth_headers
    )
    run_id = run_response.json()["id"]
    
    # Export CSV
    response = client.get(
        f"/admin/prompt-evaluation/results/export-csv?run_id={run_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "evaluation_results_" in response.headers["content-disposition"]
    
    # Check CSV content
    csv_content = response.text
    assert "result_id,run_id,run_name" in csv_content
    assert "Export Results Test Run" in csv_content


def test_require_admin_access(client: TestClient, user_headers: dict):
    """Test that non-admin users cannot access evaluation endpoints"""
    # Try to list cases as regular user
    response = client.get(
        "/admin/prompt-evaluation/cases",
        headers=user_headers
    )
    
    assert response.status_code == 403
