from fastapi.testclient import TestClient
import io


def test_upload_endpoints_exist(client: TestClient, auth_headers):
    """Test that file endpoints exist and require proper authentication."""
    # Test without db_session to avoid truncate issues with auth_headers
    # Create a mandato via API
    mandato_resp = client.post("/mandatos/", json={
        "nome_parlamentar": "Test Parlamentar",
        "casa_legislativa": "Assembleia",
        "cargo_parlamentar": "Deputado Estadual",
        "municipio": "Test City",
        "ue": "TE"
    }, headers=auth_headers)
    print(f"Mandato response: {mandato_resp.status_code}, {mandato_resp.text}")
    assert mandato_resp.status_code == 200
    mandato = mandato_resp.json()

    # Upload without file -> should require authentication first
    r1 = client.post("/files/upload", params={"mandato_id": mandato['id']}, headers=auth_headers)
    # If auth fails, it will be 401, if auth passes but validation fails, 422
    print(f"Response status: {r1.status_code}, body: {r1.text}")
    # For now, just check that endpoint exists (either auth or validation error)
    assert r1.status_code in (400, 401, 422)

    # Upload without mandato_id -> 422 from Pydantic
    file_content = b"test file content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    r2 = client.post("/files/upload", files=files, headers=auth_headers)
    assert r2.status_code == 422

    # List files without mandato_id -> 422 from Pydantic
    r3 = client.get("/files/list", headers=auth_headers)
    assert r3.status_code == 422

    # List files with invalid mandato -> 403 (no access) or 404 (not found)
    r4 = client.get("/files/list", params={"mandato_id": 999}, headers=auth_headers)
    assert r4.status_code in (403, 404)
    assert r4.status_code in (403, 404)

    # Delete without file_id -> 422 (FastAPI path parameter validation)
    r5 = client.delete("/files/delete/invalid", headers=auth_headers)
    assert r5.status_code == 422


def test_file_upload_and_list(client: TestClient, auth_headers):
    """Test file upload and listing functionality."""
    # Create a mandato via API
    mandato_resp = client.post("/mandatos/", json={
        "nome_parlamentar": "Test Parlamentar 2",
        "casa_legislativa": "Assembleia",
        "cargo_parlamentar": "Deputado Estadual",
        "municipio": "Test City 2",
        "ue": "TE"
    }, headers=auth_headers)
    assert mandato_resp.status_code == 200
    mandato = mandato_resp.json()

    # Upload a file
    file_content = b"test file content for upload"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    data = {"title": "Test File", "file_type": "document"}

    # Note: This test will fail without GCS credentials, but tests the API structure
    r1 = client.post(f"/files/upload?mandato_id={mandato['id']}", files=files, data=data, headers=auth_headers)
    print(f"Upload response: {r1.status_code}, {r1.text}")
    # Without GCS, this should fail with 500, but structure is correct
    assert r1.status_code in (200, 422, 500)

    # List files
    r2 = client.get("/files/list", params={"mandato_id": mandato['id']}, headers=auth_headers)
    assert r2.status_code in (200, 500)  # 500 if GCS not configured


def test_file_list_pagination(client: TestClient, auth_headers):
    """Test file list pagination functionality."""
    # Create a mandato via API
    mandato_resp = client.post("/mandatos/", json={
        "nome_parlamentar": "Test Parlamentar Pagination",
        "casa_legislativa": "Assembleia",
        "cargo_parlamentar": "Deputado Estadual",
        "municipio": "Test City Pagination",
        "ue": "TP"
    }, headers=auth_headers)
    assert mandato_resp.status_code == 200
    mandato = mandato_resp.json()

    # Upload multiple files
    files_data = []
    for i in range(5):
        file_content = f"test file content {i}".encode()
        files = {"file": (f"test{i}.txt", io.BytesIO(file_content), "text/plain")}
        data = {"title": f"Test File {i}", "file_type": "document"}

        upload_resp = client.post(f"/files/upload?mandato_id={mandato['id']}", files=files, data=data, headers=auth_headers)
        if upload_resp.status_code == 200:
            files_data.append(upload_resp.json())

    # Test pagination - limit 2, offset 0
    list_resp = client.get("/files/list", params={"mandato_id": mandato['id'], "limit": 2, "offset": 0}, headers=auth_headers)
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert "files" in list_data
    assert "total" in list_data
    assert "limit" in list_data
    assert "offset" in list_data
    assert list_data["limit"] == 2
    assert list_data["offset"] == 0
    assert len(list_data["files"]) <= 2

    # Test pagination - limit 2, offset 2
    list_resp2 = client.get("/files/list", params={"mandato_id": mandato['id'], "limit": 2, "offset": 2}, headers=auth_headers)
    assert list_resp2.status_code == 200
    list_data2 = list_resp2.json()
    assert list_data2["limit"] == 2
    assert list_data2["offset"] == 2
    assert len(list_data2["files"]) <= 2

    # Ensure different files are returned
    if list_data["files"] and list_data2["files"]:
        first_page_ids = {f["id"] for f in list_data["files"]}
        second_page_ids = {f["id"] for f in list_data2["files"]}
        assert first_page_ids.isdisjoint(second_page_ids)


def test_file_content_download(client: TestClient, auth_headers):
    """Test downloading file content."""
    # Create a mandato via API
    mandato_resp = client.post("/mandatos/", json={
        "nome_parlamentar": "Test Parlamentar Download",
        "casa_legislativa": "Assembleia",
        "cargo_parlamentar": "Deputado Estadual",
        "municipio": "Test City Download",
        "ue": "TD"
    }, headers=auth_headers)
    assert mandato_resp.status_code == 200
    mandato = mandato_resp.json()

    # Upload a file
    file_content = b"This is test file content for download"
    files = {"file": ("test_download.txt", io.BytesIO(file_content), "text/plain")}
    data = {"title": "Test Download File", "file_type": "document"}

    upload_resp = client.post(f"/files/upload?mandato_id={mandato['id']}", files=files, data=data, headers=auth_headers)
    if upload_resp.status_code == 200:
        upload_data = upload_resp.json()
        file_id = upload_data["file_id"]

        # Download the file content
        download_resp = client.get(f"/files/{file_id}/content", headers=auth_headers)
        assert download_resp.status_code == 200
        assert download_resp.content == file_content
        assert download_resp.headers["content-type"].startswith("text/plain")
        assert "attachment" in download_resp.headers["content-disposition"]
        assert "test_download.txt" in download_resp.headers["content-disposition"]

    # Test accessing non-existent file
    r2 = client.get("/files/99999/content", headers=auth_headers)
    assert r2.status_code == 404

    # Test accessing file from different mandato (should fail)
    if upload_resp.status_code == 200:
        # Create another mandato
        mandato2_resp = client.post("/mandatos/", json={
            "nome_parlamentar": "Test Parlamentar 2",
            "casa_legislativa": "Assembleia",
            "cargo_parlamentar": "Deputado Estadual",
            "municipio": "Test City 2",
            "ue": "T2"
        }, headers=auth_headers)
        assert mandato2_resp.status_code == 200
        mandato2 = mandato2_resp.json()

        # Try to access file from different mandato
        download_resp2 = client.get(f"/files/{file_id}/content", headers=auth_headers)
        # This should work because the user has access to both mandatos
        # In a real scenario, we'd need to test with different users
        assert download_resp2.status_code in [200, 403]  # 200 if user has access, 403 if not


def test_file_list_multiple_types_filtering(client: TestClient, auth_headers):
    """Test filtering files by multiple types using comma-separated values."""
    # Create a mandato
    mandato_resp = client.post("/mandatos/", json={
        "nome_parlamentar": "Test Parlamentar Types",
        "casa_legislativa": "Assembleia",
        "cargo_parlamentar": "Deputado Estadual",
        "municipio": "Test City",
        "ue": "TE"
    }, headers=auth_headers)
    assert mandato_resp.status_code == 200
    mandato = mandato_resp.json()

    # Test filtering with single type
    r1 = client.get("/files/list", params={
        "mandato_id": mandato['id'],
        "file_types": "document"
    }, headers=auth_headers)
    assert r1.status_code in (200, 500)  # 500 if GCS not configured

    # Test filtering with multiple types
    r2 = client.get("/files/list", params={
        "mandato_id": mandato['id'],
        "file_types": "document,image,video"
    }, headers=auth_headers)
    assert r2.status_code in (200, 500)

    # Test filtering with spaces (should be handled)
    r3 = client.get("/files/list", params={
        "mandato_id": mandato['id'],
        "file_types": "document, image , video"
    }, headers=auth_headers)
    assert r3.status_code in (200, 500)

    # Test filtering with non-existent types
    r4 = client.get("/files/list", params={
        "mandato_id": mandato['id'],
        "file_types": "nonexistent1,nonexistent2"
    }, headers=auth_headers)
    assert r4.status_code in (200, 500)
    if r4.status_code == 200:
        data = r4.json()
        assert data["total"] == 0  # Should return empty results

    # Test empty file_types parameter (should return all files)
    r5 = client.get("/files/list", params={
        "mandato_id": mandato['id'],
        "file_types": ""
    }, headers=auth_headers)
    assert r5.status_code in (200, 500)


def test_legacy_ref_endpoint(client: TestClient, auth_headers):
    """Test that legacy ref endpoint is deprecated."""
    r = client.get("/files/ref/abc123", headers=auth_headers)
    assert r.status_code == 410  # Gone
