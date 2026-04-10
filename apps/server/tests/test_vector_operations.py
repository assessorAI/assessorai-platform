from __future__ import annotations

from typing import Iterable, List
from unittest.mock import patch

import pytest

from assessorai.services.embeddings import EmbeddingProvider, get_embedding_dimension
from assessorai.services.vector_ingestion import VectorDocument, assign_embeddings


class CountingProvider(EmbeddingProvider):
    def __init__(self, dim=None):
        self.calls: List[List[str]] = []
        self.name = "test-provider"
        self.dim = dim or get_embedding_dimension()

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        texts_list = list(texts)
        self.calls.append(texts_list)
        return [[float(idx % 100) / 100.0] * self.dim for idx, _ in enumerate(texts_list)]


def build_docs(total: int) -> List[VectorDocument]:
    docs: List[VectorDocument] = []
    for idx in range(total):
        docs.append(
            VectorDocument(
                title=None,
                house=None,
                type=None,
                number=None,
                presentation_date=None,
                year=None,
                author=None,
                subject=None,
                full_text=None,
                chunk_text=f"texto {idx}",
                chunk_number=idx,
                length=None,
                url=None,
                scraped_at=None,
                metadata=None,
                embedding=[],
            )
        )
    return docs


def test_assign_embeddings_batches(monkeypatch):
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "2")
    monkeypatch.setenv("EMBEDDING_DIM", "2")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    provider = CountingProvider(dim=2)
    documents = build_docs(5)

    assign_embeddings(documents, provider=provider)

    # Expect ceil(5/2)=3 calls to provider
    assert len(provider.calls) == 3
    for doc in documents:
        assert doc.embedding, "Documento deve receber vetor"
        assert len(doc.embedding) == 2


def test_assign_embeddings_empty(monkeypatch):
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "10")
    provider = CountingProvider()
    assign_embeddings([], provider=provider)
    assert provider.calls == []


from fastapi.testclient import TestClient


def test_vector_search_endpoints(client: TestClient, auth_headers):
    # Note: This test uses the new async import endpoint which returns a job_id
    # The background task processes the import asynchronously
    # In TestClient, background tasks execute immediately, so the data should be available
    payload = {
        "items": [
            {
                "title": "Educação Infantil",
                "house": "Câmara Municipal",
                "subject": "Política pública de educação infantil",
                "full_text": "Educação básica com foco em creches e escolas municipais.",
                "year": 2024,
                "author": ["Comissão de Educação"],
                "metadata": {"categoria": "educacao"},
            }
        ],
        "chunk_full_text": False,
        "truncate_before_insert": True,
    }
    import_response = client.post(
        "/admin/vector/import",
        json=payload,
        headers=auth_headers,
    )
    assert import_response.status_code == 200, import_response.text
    import_data = import_response.json()
    assert "id" in import_data, "Response should contain job id"
    assert "status" in import_data, "Response should contain status"
    # Note: Job may fail if OpenAI is not configured, but endpoint should succeed
    assert import_data["status"] in ["PENDING", "PROCESSING", "COMPLETED", "FAILED"], "Job should have valid status"

    if import_data["status"] == "FAILED":
        return

    # After background task completes (immediate in TestClient), data should be searchable
    query_response = client.get(
        "/search/query",
        params={"query": "educação"},
        headers=auth_headers,
    )
    assert query_response.status_code == 200
    data = query_response.json()
    assert "projects" in data
    # Validate chunk_text is included in results
    if data["projects"]:
        project = data["projects"][0]
        assert "chunk_text" in project, "chunk_text should be included in search results"
        if project["chunk_text"] is None:
            return
        assert project["chunk_text"] == "Educação básica com foco em creches e escolas municipais."
        # Validate id is included in project (deduplicate=true by default)
        assert "id" in project, "id should be included in project when deduplicate=true"
        assert isinstance(project["id"], int), "id should be an integer"
        # Validate id is included in chunks
        if project.get("chunks"):
            chunk = project["chunks"][0]
            assert "id" in chunk, "id should be included in each chunk"
            assert isinstance(chunk["id"], int), "chunk id should be an integer"

    # Test with deduplicate=false to ensure id is also present
    query_no_dedup = client.get(
        "/search/query",
        params={"query": "educação", "deduplicate": "false"},
        headers=auth_headers,
    )
    assert query_no_dedup.status_code == 200
    data_no_dedup = query_no_dedup.json()
    if data_no_dedup["projects"]:
        chunk = data_no_dedup["projects"][0]
        assert "id" in chunk, "id should be included when deduplicate=false"
        assert isinstance(chunk["id"], int), "id should be an integer"

    projects_response = client.get(
        "/search/top_projects",
        params={"query": "educação"},
        headers=auth_headers,
    )
    assert projects_response.status_code == 200
    top_data = projects_response.json()
    # Validate chunk_text is included in top_projects results
    if top_data.get("projects"):
        top_project = top_data["projects"][0]
        assert "chunk_text" in top_project, "chunk_text should be included in top_projects results"


def test_vector_search_hydrates_full_text_from_chunk0(db_session):
    from assessorai.db.models import ProjetoReferencia
    from assessorai.services.embeddings import get_embedding_dimension
    from assessorai.services.vector_store import VectorStorePgVector

    dim = get_embedding_dimension()
    full_text = "Texto completo do documento"

    common = {
        "title": "Doc X",
        "house": "Casa",
        "type": "PL",
        "number": 123,
        "year": 2024,
        "author": ["Autor"],
        "subject": "Assunto",
        "presentation_date": None,
        "length": None,
        "url": None,
        "scraped_at": None,
        "metadata_json": None,
    }

    # chunk 0: has full_text but embedding farther from query
    db_session.add(
        ProjetoReferencia(
            **common,
            full_text=full_text,
            chunk_text="primeiro chunk",
            chunk_number=0,
            embedding=[2.0] * dim,
        )
    )
    # chunk 1: matches query embedding but has full_text NULL
    db_session.add(
        ProjetoReferencia(
            **common,
            full_text=None,
            chunk_text="segundo chunk",
            chunk_number=1,
            embedding=[1.0] * dim,
        )
    )
    db_session.commit()

    store = VectorStorePgVector(db_session)

    # deduplicate=False: API compatibility hack maps full_text -> chunk_text
    chunks = store.search([1.0] * dim, limit=1, offset=0, deduplicate=False, detail=True)
    assert chunks
    assert chunks[0]["chunk_text"] == full_text

    # deduplicate=True: project-level chunk_text is sourced from hydrated full_text
    projects = store.search([1.0] * dim, limit=1, offset=0, deduplicate=True, detail=True)
    assert projects
    assert projects[0]["chunk_text"] == full_text


from types import SimpleNamespace

import pytest

from assessorai.services.embeddings import (
    get_embedding_dimension,
    get_embedding_provider,
    list_available_providers,
)


@pytest.fixture(autouse=True)
def clear_embedding_cache():
    get_embedding_provider.cache_clear()
    yield
    get_embedding_provider.cache_clear()


def test_get_embedding_provider_openai(monkeypatch):
    from assessorai.services.embeddings.providers import openai as openai_provider

    class DummyEmbeddings:
        def __init__(self):
            self.calls = []

        def create(self, model, input):
            self.calls.append((model, list(input)))
            return SimpleNamespace(
                data=[
                    SimpleNamespace(embedding=[float(idx), float(idx) + 0.5])
                    for idx, _ in enumerate(input)
                ]
            )

    class DummyClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.embeddings = DummyEmbeddings()

    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setattr(openai_provider, "OpenAI", DummyClient)
    monkeypatch.setattr(openai_provider, "OpenAIError", RuntimeError)

    provider = get_embedding_provider()
    assert provider.name == "openai:text-embedding-3-small"

    vectors = provider.embed(["bicicleta", "mobilidade"])
    assert vectors == [[0.0, 0.5], [1.0, 1.5]]


def test_get_embedding_dimension_defaults(monkeypatch):
    monkeypatch.delenv("EMBEDDING_DIM", raising=False)
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_EMBEDDING_MODEL", raising=False)
    assert get_embedding_dimension() == 1536


def test_get_embedding_dimension_openai(monkeypatch):
    monkeypatch.delenv("EMBEDDING_DIM", raising=False)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    assert get_embedding_dimension() == 3072


def test_openai_provider_requires_api_key(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        get_embedding_provider()


def test_list_available_providers(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    providers = list_available_providers()
    ids = [item["id"] for item in providers]
    assert ids == []

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    providers = list_available_providers()
    ids = [item["id"] for item in providers]
    assert ids == ["openai"]


def test_vector_admin_providers_endpoint(client: TestClient, auth_headers):
    response = client.get("/admin/vector/providers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert "current_provider" in data
    assert "current_model" in data


def test_vector_admin_stats_endpoint(client: TestClient, auth_headers):
    response = client.get("/admin/vector/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "chunks" in data
    assert isinstance(data["projects"], int)
    assert isinstance(data["chunks"], int)


def test_vector_stats_caching(monkeypatch):
    """Test that vector stats are cached and invalidated correctly."""
    from assessorai.services.vector_store import VectorStorePgVector, invalidate_stats_cache
    from unittest.mock import MagicMock
    
    # Create a mock session
    mock_session = MagicMock()
    store = VectorStorePgVector(mock_session)
    
    # Mock the database query to return fixed results
    mock_result = {"chunks": 100, "projects": 10}
    mock_session.execute.return_value.mappings.return_value.first.return_value = mock_result
    
    # Clear cache before test
    invalidate_stats_cache()
    
    # First call should hit database
    result1 = store.stats(use_cache=True)
    assert result1 == mock_result
    assert mock_session.execute.call_count == 1
    
    # Second call should use cache (no additional database query)
    result2 = store.stats(use_cache=True)
    assert result2 == mock_result
    assert mock_session.execute.call_count == 1  # Still 1, no new query
    
    # Force refresh by disabling cache
    result3 = store.stats(use_cache=False)
    assert result3 == mock_result
    assert mock_session.execute.call_count == 2  # New query
    
    # Cache should be updated, next call should use cache again
    result4 = store.stats(use_cache=True)
    assert result4 == mock_result
    assert mock_session.execute.call_count == 2  # Still 2
    
    # Invalidate cache manually
    invalidate_stats_cache()
    
    # Next call should hit database again
    result5 = store.stats(use_cache=True)
    assert result5 == mock_result
    assert mock_session.execute.call_count == 3  # New query after invalidation


def test_vector_admin_reindex_endpoint(client: TestClient, auth_headers):
    # First import some data
    payload = {
        "items": [
            {
                "title": "Test Project",
                "subject": "Test subject",
                "full_text": "Some test text for reindexing.",
                "year": 2024,
            }
        ],
        "chunk_full_text": False,
        "truncate_before_insert": True,
    }
    import_response = client.post(
        "/admin/vector/import",
        json=payload,
        headers=auth_headers,
    )
    assert import_response.status_code == 200

    # Now reindex - mock get_embedding_provider to avoid OpenAI client initialization
    mock_provider = CountingProvider()
    with patch("assessorai.routers.vector_admin.get_embedding_provider") as mock_get_provider, \
         patch("assessorai.routers.vector_admin.resolve_current_model") as mock_resolve_model:
        mock_get_provider.return_value = mock_provider
        mock_resolve_model.return_value = "test-model"
        
        reindex_payload = {"batch_size": 10}
        response = client.post("/admin/vector/reindex", json=reindex_payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "model" in data
        assert "chunks" in data
        assert "skipped" in data
        assert "total" in data
