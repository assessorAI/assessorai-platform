from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from assessorai.services.embeddings import EmbeddingProvider
from assessorai.routers.vector_admin import VectorImportItem


def _ensure_admin_headers(client: TestClient) -> dict:
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
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class MockEmbeddingProvider(EmbeddingProvider):
    def __init__(self, name="mock-provider", model_name="mock-model"):
        self.name = name
        self.model_name = model_name

    def embed(self, texts):
        return [[0.1] * 1536 for _ in texts]


def test_list_embedding_providers(client: TestClient):
    headers = _ensure_admin_headers(client)

    with patch("assessorai.routers.vector_admin.list_available_providers") as mock_list, \
         patch("assessorai.routers.vector_admin.resolve_current_provider") as mock_current_provider, \
         patch("assessorai.routers.vector_admin.resolve_current_model") as mock_current_model:

        mock_list.return_value = [
            {"id": "openai", "label": "OpenAI", "default_model": "text-embedding-3-small"},
            {"id": "local", "label": "Local", "default_model": None}
        ]
        mock_current_provider.return_value = "openai"
        mock_current_model.return_value = "text-embedding-3-small"

        r = client.get("/admin/vector/providers", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert "providers" in data
        assert "current_provider" in data
        assert "current_model" in data
        assert len(data["providers"]) == 2
        assert data["current_provider"] == "openai"


def test_vector_stats(client: TestClient):
    from assessorai.main import app
    from assessorai.routers.deps import get_vector_store
    
    headers = _ensure_admin_headers(client)

    mock_store = MagicMock()
    mock_store.stats.return_value = {"projects": 5, "chunks": 100}

    app.dependency_overrides[get_vector_store] = lambda: mock_store
    try:
        r = client.get("/admin/vector/stats", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["projects"] == 5
        assert data["chunks"] == 100
    finally:
        app.dependency_overrides.pop(get_vector_store, None)


def test_reindex_vectors(client: TestClient):
    from assessorai.main import app
    from assessorai.routers.deps import get_vector_store
    
    headers = _ensure_admin_headers(client)

    mock_provider = MockEmbeddingProvider()
    mock_store = MagicMock()
    mock_store.reindex.return_value = {"updated": 10, "skipped": 2, "total": 12}

    app.dependency_overrides[get_vector_store] = lambda: mock_store
    try:
        with patch("assessorai.routers.vector_admin.get_embedding_provider") as mock_get_provider, \
             patch("assessorai.routers.vector_admin.resolve_current_model") as mock_resolve_model:

            mock_get_provider.return_value = mock_provider
            mock_resolve_model.return_value = "mock-model"

            payload = {"batch_size": 64}
            r = client.post("/admin/vector/reindex", json=payload, headers=headers)
            assert r.status_code == 200
            data = r.json()
            assert data["chunks"] == 10
            assert data["skipped"] == 2
            assert data["total"] == 12
            assert "provider" in data
            assert "model" in data
    finally:
        app.dependency_overrides.pop(get_vector_store, None)


def test_import_vector_documents(client: TestClient):
    headers = _ensure_admin_headers(client)

    mock_provider = MockEmbeddingProvider()

    with patch("assessorai.routers.vector_admin.background_ingest_task") as mock_background:
        payload = {
            "items": [
                {
                    "title": "Test Doc 1",
                    "full_text": "This is test content 1",
                    "metadata": {"source": "test"}
                },
                {
                    "title": "Test Doc 2",
                    "full_text": "This is test content 2",
                    "metadata": {"source": "test"}
                }
            ],
            "chunk_full_text": True,
            "chunk_size": 1000,
            "chunk_overlap": 100
        }
        r = client.post("/admin/vector/import", json=payload, headers=headers)
        assert r.status_code == 200
        data = r.json()
        # Now returns job info instead of immediate result
        assert "id" in data
        assert "status" in data
        assert data["total_items"] == 2
        assert data["status"] == "PENDING"
        
        # Verify background task was scheduled (called via BackgroundTasks.add_task)
        # Note: The mock is called because BackgroundTasks executes immediately in TestClient
        assert mock_background.called


def test_import_vector_documents_validation_error(client: TestClient):
    headers = _ensure_admin_headers(client)

    # Empty items
    payload = {"items": []}
    r = client.post("/admin/vector/import", json=payload, headers=headers)
    assert r.status_code == 422


def test_list_import_jobs(client: TestClient, db_session):
    from assessorai.db.models import VectorImportJob, VectorImportJobStatus
    
    headers = _ensure_admin_headers(client)
    
    # Create test jobs directly in the database
    job1 = VectorImportJob(
        name="Test Import 1",
        status=VectorImportJobStatus.COMPLETED,
        total_items=10,
        processed_chunks=25,
        created_by=1,
    )
    job2 = VectorImportJob(
        name="Test Import 2",
        status=VectorImportJobStatus.PENDING,
        total_items=5,
        processed_chunks=0,
        created_by=1,
    )
    db_session.add(job1)
    db_session.add(job2)
    db_session.commit()
    
    # Test listing jobs
    r = client.get("/admin/vector/jobs", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    # Find our test jobs
    test_jobs = [j for j in data if j["name"] in ["Test Import 1", "Test Import 2"]]
    assert len(test_jobs) == 2
    # Most recent first (job2 was created after job1)
    job2_data = next(j for j in test_jobs if j["name"] == "Test Import 2")
    job1_data = next(j for j in test_jobs if j["name"] == "Test Import 1")
    assert job2_data["status"] == "PENDING"
    assert job1_data["status"] == "COMPLETED"
    assert job1_data["processed_chunks"] == 25
    
    # Test pagination
    r = client.get("/admin/vector/jobs?limit=1&offset=0", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1


def test_async_vector_import_creates_job(client: TestClient, db_session):
    from assessorai.db.models import VectorImportJob, VectorImportJobStatus
    
    headers = _ensure_admin_headers(client)
    
    # Clean up any pending/processing jobs from previous tests
    db_session.query(VectorImportJob).filter(
        VectorImportJob.status.in_([VectorImportJobStatus.PENDING, VectorImportJobStatus.PROCESSING])
    ).delete()
    db_session.commit()
    
    with patch("assessorai.routers.vector_admin.background_ingest_task") as mock_background:
        payload = {
            "items": [
                {
                    "title": "Async Doc 1",
                    "full_text": "Content 1",
                    "metadata": {"source": "test"}
                },
                {
                    "title": "Async Doc 2",
                    "full_text": "Content 2",
                    "metadata": {"source": "test"}
                },
                {
                    "title": "Async Doc 3",
                    "full_text": "Content 3",
                    "metadata": {"source": "test"}
                }
            ],
            "chunk_full_text": True,
            "name": "Async Test Import"
        }
        
        r = client.post("/admin/vector/import", json=payload, headers=headers)
        assert r.status_code == 200
        data = r.json()
        
        # Should return job info
        assert "id" in data
        assert data["status"] == "PENDING"
        assert data["name"] == "Async Test Import"
        assert data["total_items"] == 3
        
        # Verify background task was scheduled (TestClient executes background tasks immediately)
        assert mock_background.called
        
        # Verify job was created via API response
        job_id = data["id"]
        r = client.get("/admin/vector/jobs", headers=headers)
        assert r.status_code == 200
        jobs = r.json()
        created_job = next((j for j in jobs if j["id"] == job_id), None)
        assert created_job is not None
        assert created_job["name"] == "Async Test Import"
        assert created_job["total_items"] == 3


def test_vector_endpoints_unauthorized(client: TestClient):
    # No auth
    r = client.get("/admin/vector/providers")
    assert r.status_code == 401

    # Non-admin
    payload = {
        "email": "user@example.com",
        "first_name": "Test",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "tester",
        "password": "secret123",
        "mandato": [
            {
                "nome_parlamentar": "Test User",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "São Paulo",
                "ue": "SP",
            }
        ],
    }
    client.post("/auth/register", json=payload)
    token_response = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/admin/vector/providers", headers=headers)
    assert r.status_code == 403


# New tests for JSON format handling
def test_vector_import_item_valid():
    """Test that valid items are accepted"""
    item = VectorImportItem(
        title="PL 101/2020",
        house="Câmara Municipal",
        type="PL",
        number=101,
        year=2020,
        author=["Ver. JOÃO SILVA"],
        subject="Assunto do projeto",
        full_text="Texto completo do projeto de lei",
        metadata={
            "pdf_files": ["sp-sao-paulo/pdf/2020/pl-101-2020.pdf"],
            "uuid": "abc123"
        }
    )
    assert item.title == "PL 101/2020"
    assert item.year == 2020
    assert isinstance(item.metadata, dict)
    assert item.metadata["uuid"] == "abc123"


def test_vector_import_item_rejects_wrapper():
    """Test that wrapper format is rejected"""
    with pytest.raises(ValidationError) as exc_info:
        VectorImportItem(**{
            "items": [{"title": "PL 101/2020"}],
            "export_info": {}
        })
    
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert "Formato incorreto" in errors[0]["msg"]


def test_vector_import_request_with_new_format(client: TestClient, db_session):
    """Test API endpoint with new wrapper format (multiple items)"""
    from assessorai.db.models import VectorImportJob, VectorImportJobStatus
    
    headers = _ensure_admin_headers(client)
    
    # Clean up any pending/processing jobs from previous tests
    db_session.query(VectorImportJob).filter(
        VectorImportJob.status.in_([VectorImportJobStatus.PENDING, VectorImportJobStatus.PROCESSING])
    ).delete()
    db_session.commit()
    
    with patch("assessorai.routers.vector_admin.background_ingest_task") as mock_background:
        payload = {
            "items": [
                {
                    "title": "PL 101/2020",
                    "house": "Câmara Municipal",
                    "type": "PL",
                    "number": 101,
                    "year": 2020,
                    "author": ["Ver. JOÃO SILVA"],
                    "subject": "Assunto do projeto",
                    "full_text": "Texto completo do projeto de lei",
                    "metadata": {
                        "pdf_files": ["test.pdf"],
                        "uuid": "abc123"
                    }
                },
                {
                    "title": "PL 102/2020",
                    "house": "Câmara Municipal",
                    "type": "PL",
                    "number": 102,
                    "year": 2020,
                    "author": ["Ver. MARIA SANTOS"],
                    "subject": "Outro assunto",
                    "full_text": "Outro texto completo",
                    "metadata": {
                        "pdf_files": ["test2.pdf"],
                        "uuid": "def456"
                    }
                }
            ],
            "chunk_full_text": False,
            "truncate_before_insert": True,
            "name": "Test import with wrapper format"
        }
        
        response = client.post(
            "/admin/vector/import",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data
        assert data["total_items"] == 2
        assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]


def test_vector_import_request_old_format(client: TestClient, db_session):
    """Test API endpoint still works with old format (backward compatibility)"""
    from assessorai.db.models import VectorImportJob, VectorImportJobStatus
    
    headers = _ensure_admin_headers(client)
    
    # Clean up any pending/processing jobs from previous tests
    db_session.query(VectorImportJob).filter(
        VectorImportJob.status.in_([VectorImportJobStatus.PENDING, VectorImportJobStatus.PROCESSING])
    ).delete()
    db_session.commit()
    
    with patch("assessorai.routers.vector_admin.background_ingest_task") as mock_background:
        payload = {
            "items": [
                {
                    "title": "PL 201/2020",
                    "house": "Câmara Municipal",
                    "full_text": "Texto do projeto antigo",
                    "year": 2020
                }
            ],
            "chunk_full_text": False,
            "truncate_before_insert": True,
            "name": "Test import with old format"
        }
        
        response = client.post(
            "/admin/vector/import",
            json=payload,
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data
        assert data["total_items"] == 1


def test_vector_import_prevents_concurrent_imports(client: TestClient, db_session):
    """Test that concurrent imports are blocked"""
    from assessorai.db.models import VectorImportJob, VectorImportJobStatus
    
    headers = _ensure_admin_headers(client)
    
    # Create a job in PROCESSING state
    active_job = VectorImportJob(
        name="Active Import Job",
        status=VectorImportJobStatus.PROCESSING,
        total_items=100,
        created_by=1,
    )
    db_session.add(active_job)
    db_session.commit()
    
    # Try to start another import
    with patch("assessorai.routers.vector_admin.background_ingest_task") as mock_background:
        payload = {
            "items": [
                {
                    "title": "Test Doc",
                    "full_text": "Test content",
                    "year": 2024
                }
            ],
            "chunk_full_text": False,
            "truncate_before_insert": True,
            "name": "Second Import Attempt"
        }
        
        response = client.post(
            "/admin/vector/import",
            json=payload,
            headers=headers,
        )
        
        # Should be rejected with 409 Conflict
        assert response.status_code == 409
        error_data = response.json()
        assert "detail" in error_data
        detail = error_data["detail"]
        assert detail["error"] == "concurrent_import_not_allowed"
        assert "active_jobs" in detail
        assert len(detail["active_jobs"]) == 1
        assert detail["active_jobs"][0]["id"] == active_job.id
        
        # Background task should NOT have been called
        assert not mock_background.called


def test_vector_import_allows_after_completion(client: TestClient, db_session):
    """Test that imports are allowed after previous job completes"""
    from assessorai.db.models import VectorImportJob, VectorImportJobStatus
    from datetime import datetime
    
    headers = _ensure_admin_headers(client)
    
    # Create a COMPLETED job (should not block)
    completed_job = VectorImportJob(
        name="Completed Import Job",
        status=VectorImportJobStatus.COMPLETED,
        total_items=100,
        processed_chunks=250,
        created_by=1,
        completed_at=datetime.utcnow()
    )
    db_session.add(completed_job)
    db_session.commit()
    
    # Try to start new import
    with patch("assessorai.routers.vector_admin.background_ingest_task") as mock_background:
        payload = {
            "items": [
                {
                    "title": "New Import",
                    "full_text": "Content",
                    "year": 2024
                }
            ],
            "chunk_full_text": False,
            "truncate_before_insert": True,
            "name": "New Import After Completion"
        }
        
        response = client.post(
            "/admin/vector/import",
            json=payload,
            headers=headers,
        )
        
        # Should be accepted
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "PENDING"
        
        # Background task should have been called
        assert mock_background.called


def test_check_duplicates_endpoint(client: TestClient, db_session):
    """Test the check-duplicates endpoint"""
    from assessorai.db.models import ProjetoReferencia
    
    headers = _ensure_admin_headers(client)
    
    # Insert some test documents into the database
    test_doc = ProjetoReferencia(
        title="PL 500/2024",
        house="Câmara Municipal",
        type="PL",
        number=500,
        year=2024,
        chunk_text="Teste de documento existente",
        chunk_number=1,
        embedding=[0.1] * 1536,
    )
    db_session.add(test_doc)
    db_session.commit()
    
    # Test with duplicate
    payload = {
        "items": [
            {
                "title": "PL 500/2024",
                "house": "Câmara Municipal",
                "type": "PL",
                "number": 500,
                "year": 2024,
                "full_text": "Texto",
            },
            {
                "title": "PL 501/2024",
                "house": "Câmara Municipal",
                "type": "PL",
                "number": 501,
                "year": 2024,
                "full_text": "Outro texto",
            }
        ],
        "sample_size": 2
    }
    
    response = client.post("/admin/vector/check-duplicates", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_checked" in data
    assert "existing_count" in data
    assert "existing_documents" in data
    assert data["total_checked"] == 2
    assert data["existing_count"] == 1  # Only first document exists
    assert len(data["existing_documents"]) == 1
    assert data["existing_documents"][0]["title"] == "PL 500/2024"


def test_vector_summary_endpoint(client: TestClient, db_session):
    """Test the vector summary endpoint"""
    from assessorai.db.models import ProjetoReferencia
    
    headers = _ensure_admin_headers(client)
    
    # Insert test documents with different houses and years
    docs = [
        ProjetoReferencia(
            title="PL 100/2023",
            house="Câmara dos Deputados",
            type="PL",
            number=100,
            year=2023,
            chunk_text="Teste 1",
            chunk_number=1,
            embedding=[0.1] * 1536,
        ),
        ProjetoReferencia(
            title="PL 100/2023",
            house="Câmara dos Deputados",
            type="PL",
            number=100,
            year=2023,
            chunk_text="Teste 1 chunk 2",
            chunk_number=2,
            embedding=[0.1] * 1536,
        ),
        ProjetoReferencia(
            title="PL 200/2024",
            house="Senado Federal",
            type="PL",
            number=200,
            year=2024,
            chunk_text="Teste 2",
            chunk_number=1,
            embedding=[0.2] * 1536,
        ),
    ]
    for doc in docs:
        db_session.add(doc)
    db_session.commit()
    
    response = client.get("/admin/vector/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "houses" in data
    assert "total_projects" in data
    assert data["total_projects"] == 2  # Two unique titles
    
    # Check that we have house groupings
    houses = data["houses"]
    assert len(houses) >= 2
    
    # Find Câmara dos Deputados
    camara = next((h for h in houses if h["house"] == "Câmara dos Deputados"), None)
    assert camara is not None
    assert len(camara["years"]) >= 1
    
    # Find year 2023 for Câmara
    year_2023 = next((y for y in camara["years"] if y["year"] == 2023), None)
    assert year_2023 is not None
    assert year_2023["count"] == 1  # One unique project in 2023

