from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from assessorai.db.models import PromptTemplate as PromptTemplateORM, AuditLog


def _ensure_admin_headers(client: TestClient) -> dict:
    """Create admin user and return auth headers"""
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


def _ensure_regular_user_headers(client: TestClient) -> dict:
    """Create regular user and return auth headers"""
    import secrets
    # Use unique email to avoid conflicts between tests
    unique_email = f"user-{secrets.token_hex(4)}@example.com"
    
    payload = {
        "email": unique_email,
        "first_name": "Regular",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "staff",
        "password": "secret456",
        "mandato": [
            {
                "nome_parlamentar": "Regular User",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "São Paulo",
                "ue": "SP",
            }
        ],
    }
    register_response = client.post("/auth/register", json=payload)
    
    if register_response.status_code not in (200, 201):
        raise Exception(f"Failed to register user: {register_response.status_code} - {register_response.text}")
    
    token_response = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    
    if token_response.status_code != 200:
        raise Exception(f"Failed to login as regular user: {token_response.status_code} - {token_response.text}")
    
    response_data = token_response.json()
    if "access_token" not in response_data:
        raise Exception(f"No access_token in response: {response_data}")
    
    token = response_data["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Permission Tests
# ============================================================================

def test_list_template_types_requires_admin(client: TestClient):
    """Non-admin users cannot list template types"""
    user_headers = _ensure_regular_user_headers(client)
    r = client.get("/admin/prompts/types", headers=user_headers)
    assert r.status_code == 403


def test_list_template_types_as_admin(client: TestClient):
    """Admin users can list template types"""
    headers = _ensure_admin_headers(client)
    r = client.get("/admin/prompts/types", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 5  # Should have 5 known template types
    
    # Check structure
    first_type = data[0]
    assert "type" in first_type
    assert "display_name" in first_type
    assert "file_exists" in first_type
    assert "db_versions_count" in first_type
    assert "has_active_default" in first_type


# ============================================================================
# CRUD Tests
# ============================================================================

def test_create_first_version(client: TestClient, db_session):
    """Create the first version of a template"""
    headers = _ensure_admin_headers(client)
    
    payload = {
        "template_type": "generate_oficio",
        "content": "Test template content with {{variable}}",
        "description": "First version of the template"
    }
    
    r = client.post("/admin/prompts/", json=payload, headers=headers)
    assert r.status_code == 200
    data = r.json()
    
    assert data["template_type"] == "generate_oficio"
    assert data["version"] == 1
    assert data["content"] == payload["content"]
    assert data["description"] == payload["description"]
    assert data["is_active"] is True
    assert data["is_default"] is False  # New versions are not default by default
    assert "id" in data
    assert "created_at" in data


def test_create_second_version_increments(client: TestClient, db_session):
    """Creating a second version auto-increments the version number"""
    headers = _ensure_admin_headers(client)
    
    # Create first version
    payload1 = {
        "template_type": "generate_oficio",
        "content": "Version 1 content",
        "description": "First version"
    }
    r1 = client.post("/admin/prompts/", json=payload1, headers=headers)
    assert r1.status_code == 200
    
    # Create second version
    payload2 = {
        "template_type": "generate_oficio",
        "content": "Version 2 content with improvements",
        "description": "Second version"
    }
    r2 = client.post("/admin/prompts/", json=payload2, headers=headers)
    assert r2.status_code == 200
    data2 = r2.json()
    
    assert data2["version"] == 2
    assert data2["content"] == payload2["content"]


def test_create_template_invalid_type(client: TestClient):
    """Creating template with invalid type fails"""
    headers = _ensure_admin_headers(client)
    
    payload = {
        "template_type": "invalid_type",
        "content": "Some content",
        "description": "Invalid template"
    }
    
    r = client.post("/admin/prompts/", json=payload, headers=headers)
    assert r.status_code == 400
    assert "not recognized" in r.json()["detail"]


def test_list_all_templates(client: TestClient, db_session):
    """List all templates across all types"""
    headers = _ensure_admin_headers(client)
    
    # Create templates of different types
    client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Content 1"
    }, headers=headers)
    
    client.post("/admin/prompts/", json={
        "template_type": "expert_pl_constitucionalidade",
        "content": "Content 2"
    }, headers=headers)
    
    # List all
    r = client.get("/admin/prompts/", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_list_templates_filtered_by_type(client: TestClient, db_session):
    """Filter templates by type"""
    headers = _ensure_admin_headers(client)
    
    # Create templates
    client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Content 1"
    }, headers=headers)
    
    client.post("/admin/prompts/", json={
        "template_type": "expert_pl_constitucionalidade",
        "content": "Content 2"
    }, headers=headers)
    
    # Filter by type
    r = client.get(
        "/admin/prompts/?template_type=generate_oficio",
        headers=headers
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["template_type"] == "generate_oficio"


def test_list_template_versions(client: TestClient, db_session):
    """List all versions of a specific template type"""
    headers = _ensure_admin_headers(client)
    
    # Create multiple versions
    for i in range(3):
        client.post("/admin/prompts/", json={
            "template_type": "generate_oficio",
            "content": f"Version {i+1} content",
            "description": f"Version {i+1}"
        }, headers=headers)
    
    # List versions
    r = client.get(
        "/admin/prompts/generate_oficio/versions",
        headers=headers
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    # Should be in descending order
    assert data[0]["version"] == 3
    assert data[1]["version"] == 2
    assert data[2]["version"] == 1


def test_get_specific_version(client: TestClient, db_session):
    """Get a specific version of a template"""
    headers = _ensure_admin_headers(client)
    
    # Create versions
    client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Version 1",
    }, headers=headers)
    
    client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Version 2",
    }, headers=headers)
    
    # Get version 1
    r = client.get(
        "/admin/prompts/generate_oficio/1",
        headers=headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == 1
    assert data["content"] == "Version 1"


def test_get_nonexistent_version(client: TestClient):
    """Getting non-existent version returns 404"""
    headers = _ensure_admin_headers(client)
    
    r = client.get(
        "/admin/prompts/generate_oficio/999",
        headers=headers
    )
    assert r.status_code == 404


def test_update_template_metadata(client: TestClient, db_session):
    """Update template description and content"""
    headers = _ensure_admin_headers(client)
    
    # Create template
    create_r = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Original content",
        "description": "Original description"
    }, headers=headers)
    template_id = create_r.json()["id"]
    
    # Update
    update_payload = {
        "description": "Updated description",
        "content": "Updated content"
    }
    r = client.put(
        f"/admin/prompts/{template_id}",
        json=update_payload,
        headers=headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["description"] == "Updated description"
    assert data["content"] == "Updated content"


def test_soft_delete_template(client: TestClient, db_session):
    """Soft delete a template"""
    headers = _ensure_admin_headers(client)
    
    # Create template
    create_r = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Content to delete"
    }, headers=headers)
    template_id = create_r.json()["id"]
    
    # Delete
    r = client.delete(f"/admin/prompts/{template_id}", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["is_active"] is False


def test_cannot_delete_default_version(client: TestClient, db_session):
    """Cannot delete a version that is marked as default"""
    headers = _ensure_admin_headers(client)
    
    # Create and set as default
    create_r = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Default content"
    }, headers=headers)
    template_id = create_r.json()["id"]
    
    # Set as default
    client.post(
        f"/admin/prompts/{template_id}/set-default",
        headers=headers
    )
    
    # Try to delete
    r = client.delete(f"/admin/prompts/{template_id}", headers=headers)
    assert r.status_code == 400
    assert "Cannot delete the default version" in r.json()["detail"]


# ============================================================================
# Default Version Tests
# ============================================================================

def test_set_template_as_default(client: TestClient, db_session):
    """Set a template version as default"""
    headers = _ensure_admin_headers(client)
    
    # Create template
    create_r = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Content"
    }, headers=headers)
    template_id = create_r.json()["id"]
    
    # Set as default
    r = client.post(
        f"/admin/prompts/{template_id}/set-default",
        headers=headers
    )
    assert r.status_code == 200
    data = r.json()
    assert data["is_default"] is True


def test_only_one_default_per_type(client: TestClient, db_session):
    """Only one version can be default per template type"""
    headers = _ensure_admin_headers(client)
    
    # Create two versions
    r1 = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Version 1"
    }, headers=headers)
    template1_id = r1.json()["id"]
    
    r2 = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Version 2"
    }, headers=headers)
    template2_id = r2.json()["id"]
    
    # Set first as default
    client.post(f"/admin/prompts/{template1_id}/set-default", headers=headers)
    
    # Verify first is default
    templates = client.get(
        "/admin/prompts/generate_oficio/versions",
        headers=headers
    ).json()
    v1 = next(t for t in templates if t["id"] == template1_id)
    assert v1["is_default"] is True
    
    # Set second as default
    client.post(f"/admin/prompts/{template2_id}/set-default", headers=headers)
    
    # Verify second is now default and first is not
    templates = client.get(
        "/admin/prompts/generate_oficio/versions",
        headers=headers
    ).json()
    v1 = next(t for t in templates if t["id"] == template1_id)
    v2 = next(t for t in templates if t["id"] == template2_id)
    assert v1["is_default"] is False
    assert v2["is_default"] is True


def test_cannot_set_inactive_as_default(client: TestClient, db_session):
    """Cannot set an inactive template as default"""
    headers = _ensure_admin_headers(client)
    
    # Create and deactivate
    create_r = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Content"
    }, headers=headers)
    template_id = create_r.json()["id"]
    
    # Deactivate
    client.delete(f"/admin/prompts/{template_id}", headers=headers)
    
    # Try to set as default
    r = client.post(
        f"/admin/prompts/{template_id}/set-default",
        headers=headers
    )
    assert r.status_code == 400
    assert "inactive" in r.json()["detail"].lower()


# ============================================================================
# File Content Tests
# ============================================================================

def test_get_file_content(client: TestClient):
    """Get file-based template content"""
    headers = _ensure_admin_headers(client)
    
    # This assumes generate_oficio.md exists in prompts/
    r = client.get(
        "/admin/prompts/generate_oficio/file-content",
        headers=headers
    )
    # May be 200 if file exists, or 404 if not
    if r.status_code == 200:
        data = r.json()
        assert data["template_type"] == "generate_oficio"
        assert data["source"] == "file"
        assert "content" in data
        assert len(data["content"]) > 0


# ============================================================================
# Audit Logging Tests
# ============================================================================

def test_create_template_creates_audit_log(client: TestClient, db_session):
    """Creating a template creates an audit log"""
    headers = _ensure_admin_headers(client)
    
    # Clear existing logs
    db_session.query(AuditLog).delete()
    db_session.commit()
    
    # Create template
    client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Content"
    }, headers=headers)
    
    # Check audit log
    logs = db_session.query(AuditLog).filter(
        AuditLog.event_type == "prompt_template_created"
    ).all()
    assert len(logs) == 1
    log = logs[0]
    assert log.event_type == "prompt_template_created"


def test_set_default_creates_audit_log(client: TestClient, db_session):
    """Setting default creates an audit log"""
    headers = _ensure_admin_headers(client)
    
    # Create template
    create_r = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": "Content"
    }, headers=headers)
    template_id = create_r.json()["id"]
    
    # Clear logs
    db_session.query(AuditLog).delete()
    db_session.commit()
    
    # Set as default
    client.post(
        f"/admin/prompts/{template_id}/set-default",
        headers=headers
    )
    
    # Check audit log
    logs = db_session.query(AuditLog).filter(
        AuditLog.event_type == "prompt_template_default_changed"
    ).all()
    assert len(logs) == 1


# ============================================================================
# Fallback Logic Tests (integration with llm.py)
# ============================================================================

def test_load_prompt_from_database(client: TestClient, db_session):
    """Test that load_prompt loads from database when available"""
    from assessorai.llm import load_prompt
    
    headers = _ensure_admin_headers(client)
    
    # Create and set as default
    test_content = "Test content from database {{variable}}"
    create_r = client.post("/admin/prompts/", json={
        "template_type": "generate_oficio",
        "content": test_content
    }, headers=headers)
    template_id = create_r.json()["id"]
    
    client.post(
        f"/admin/prompts/{template_id}/set-default",
        headers=headers
    )
    
    # Load prompt with session
    content = load_prompt("generate_oficio", session=db_session)
    assert content == test_content


def test_load_prompt_fallback_to_file(client: TestClient, db_session):
    """Test that load_prompt falls back to file when DB has no default"""
    from assessorai.llm import load_prompt
    import os
    
    # Only test if file exists
    if os.path.exists("prompts/generate_oficio.md"):
        # Load without default in DB
        content = load_prompt("generate_oficio", session=db_session)
        assert len(content) > 0
        assert isinstance(content, str)
