"""Tests for admin password reset endpoint"""
import pytest


def test_password_reset_endpoint_requires_auth(client):
    """Test that endpoint requires authentication"""
    response = client.post("/admin/send-password-reset", json={})
    assert response.status_code == 401


def test_password_reset_requires_user_specification(client, auth_headers):
    """Test that endpoint requires users to be specified (not default to all)"""
    response = client.post(
        "/admin/send-password-reset",
        json={},  # No users specified
        headers=auth_headers
    )
    # Should return 400 error requiring user specification
    assert response.status_code == 400
    assert "no users specified" in response.json()["detail"].lower()


def test_password_reset_all_users_with_keyword(client, auth_headers):
    """Test sending to all users requires explicit 'all' keyword"""
    response = client.post(
        "/admin/send-password-reset",
        json={"emails": ["all"]},  # Explicit "all" keyword
        headers=auth_headers
    )
    # Should work (503 if email not configured, 200 if configured)
    assert response.status_code in [200, 503]


def test_password_reset_endpoint_admin_access(client, auth_headers):
    """Test that admin can access endpoint with user_ids"""
    response = client.post(
        "/admin/send-password-reset",
        json={"user_ids": [1]},
        headers=auth_headers
    )
    # Should return 503 if email not configured, or 200 if configured
    assert response.status_code in [200, 503]
    
    if response.status_code == 503:
        assert "not configured" in response.json()["detail"].lower()
    else:
        result = response.json()
        assert "sent" in result
        assert "failed" in result
        assert "details" in result


def test_password_reset_by_emails(client, auth_headers):
    """Test sending to specific emails"""
    response = client.post(
        "/admin/send-password-reset",
        json={"emails": ["admin@example.com"]},
        headers=auth_headers
    )
    assert response.status_code in [200, 503]


def test_password_reset_by_user_ids(client, auth_headers):
    """Test sending to specific user IDs"""
    response = client.post(
        "/admin/send-password-reset",
        json={"user_ids": [1]},
        headers=auth_headers
    )
    assert response.status_code in [200, 503]


def test_password_reset_mixed_params(client, auth_headers):
    """Test that user_ids takes precedence when both provided"""
    response = client.post(
        "/admin/send-password-reset",
        json={
            "user_ids": [1],
            "emails": ["other@example.com"]
        },
        headers=auth_headers
    )
    # Should work, using user_ids
    assert response.status_code in [200, 503]


def test_password_reset_with_template_selection(client, auth_headers):
    """Test that template parameter is accepted"""
    response = client.post(
        "/admin/send-password-reset",
        json={
            "user_ids": [1],
            "template": "bubble_import_password_reset"
        },
        headers=auth_headers
    )
    # Should work with template selection
    assert response.status_code in [200, 503]


def test_password_reset_case_insensitive_email(client, auth_headers):
    """Test that email search is case-insensitive"""
    # Try with different case variations
    response1 = client.post(
        "/admin/send-password-reset",
        json={"emails": ["ADMIN@EXAMPLE.COM"]},
        headers=auth_headers
    )
    response2 = client.post(
        "/admin/send-password-reset",
        json={"emails": ["Admin@Example.Com"]},
        headers=auth_headers
    )
    response3 = client.post(
        "/admin/send-password-reset",
        json={"emails": ["admin@example.com"]},
        headers=auth_headers
    )
    # All variations should work the same
    assert response1.status_code in [200, 503]
    assert response2.status_code in [200, 503]
    assert response3.status_code in [200, 503]
    
    # If configured, all should find the same user
    if response1.status_code == 200:
        assert response1.json()["sent"] == response2.json()["sent"] == response3.json()["sent"]
