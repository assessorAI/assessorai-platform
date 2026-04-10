"""
Tests for user acquisition tracking via query parameters.
Tests the ability to capture UTM params and custom query strings during registration.
"""
import pytest
from sqlalchemy import select
from assessorai.db.models import User as UserORM


def test_register_with_utm_params(client, db_session):
    """Test user registration with UTM query parameters"""
    payload = {
        "email": "test_utm@example.com",
        "password": "senha123",
        "first_name": "Test",
        "last_name": "User",
        "permission_level": "User",
        "lgpd_check": True,
        "query_params": {
            "utm_source": "google",
            "utm_campaign": "legisladores_2024",
            "utm_medium": "cpc",
            "utm_term": "software+legislativo",
            "utm_content": "ad_variant_a"
        }
    }
    
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200
    
    # Verificar no banco que acquisition_data foi salvo
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_utm@example.com"))
    assert user is not None
    assert user.acquisition_data is not None
    assert user.acquisition_data["utm_source"] == "google"
    assert user.acquisition_data["utm_campaign"] == "legisladores_2024"
    assert user.acquisition_data["utm_medium"] == "cpc"
    assert user.acquisition_data["utm_term"] == "software+legislativo"
    assert user.acquisition_data["utm_content"] == "ad_variant_a"
    assert "captured_at" in user.acquisition_data


def test_register_with_custom_params(client, db_session):
    """Test registration with custom non-UTM query parameters"""
    payload = {
        "email": "test_custom@example.com",
        "password": "senha123",
        "first_name": "Custom",
        "permission_level": "User",
        "lgpd_check": True,
        "query_params": {
            "ref": "parceiro_x",
            "promo_code": "DESCONTO20",
            "source_page": "landing_page_v2"
        }
    }
    
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200
    
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_custom@example.com"))
    assert user is not None
    assert user.acquisition_data is not None
    assert user.acquisition_data["ref"] == "parceiro_x"
    assert user.acquisition_data["promo_code"] == "DESCONTO20"
    assert user.acquisition_data["source_page"] == "landing_page_v2"


def test_register_without_query_params(client, db_session):
    """Test that registration works without query_params (backward compatibility)"""
    payload = {
        "email": "test_no_params@example.com",
        "password": "senha123",
        "first_name": "NoParams",
        "permission_level": "User",
        "lgpd_check": True,
    }
    
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200
    
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_no_params@example.com"))
    assert user is not None
    assert user.acquisition_data is None


def test_register_with_empty_query_params(client, db_session):
    """Test registration with empty query_params dict"""
    payload = {
        "email": "test_empty_params@example.com",
        "password": "senha123",
        "first_name": "EmptyParams",
        "permission_level": "User",
        "lgpd_check": True,
        "query_params": {}
    }
    
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200
    
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_empty_params@example.com"))
    assert user is not None
    # Empty dict should not create acquisition_data
    assert user.acquisition_data is None


def test_register_with_mixed_params(client, db_session):
    """Test registration with both UTM and custom parameters"""
    payload = {
        "email": "test_mixed@example.com",
        "password": "senha123",
        "first_name": "Mixed",
        "permission_level": "User",
        "lgpd_check": True,
        "query_params": {
            "utm_source": "facebook",
            "utm_campaign": "social_promo",
            "ref": "influencer_john",
            "landing": "/promo-page",
            "device": "mobile"
        }
    }
    
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200
    
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_mixed@example.com"))
    assert user is not None
    assert user.acquisition_data is not None
    
    # Verify all params were saved
    assert user.acquisition_data["utm_source"] == "facebook"
    assert user.acquisition_data["utm_campaign"] == "social_promo"
    assert user.acquisition_data["ref"] == "influencer_john"
    assert user.acquisition_data["landing"] == "/promo-page"
    assert user.acquisition_data["device"] == "mobile"
    assert "captured_at" in user.acquisition_data


def test_acquisition_data_in_response(client, db_session):
    """Test that acquisition_data is included in the API response"""
    payload = {
        "email": "test_response@example.com",
        "password": "senha123",
        "first_name": "Response",
        "permission_level": "User",
        "lgpd_check": True,
        "query_params": {
            "utm_source": "email",
            "utm_campaign": "newsletter_jan"
        }
    }
    
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 200
    
    data = resp.json()
    # acquisition_data should be in the response
    assert "acquisition_data" in data
    assert data["acquisition_data"]["utm_source"] == "email"
    assert data["acquisition_data"]["utm_campaign"] == "newsletter_jan"


def test_register_with_url_query_params(client, db_session):
    """Test user registration with UTM params in URL query string"""
    payload = {
        "email": "test_url_utm@example.com",
        "password": "senha123",
        "first_name": "URLTest",
        "last_name": "User",
        "permission_level": "User",
        "lgpd_check": True,
    }
    
    # Send UTM params in URL query string
    resp = client.post(
        "/auth/register?utm_source=google&utm_medium=cpc&utm_campaign=legisladores_2024&utm_term=software+legislativo",
        json=payload
    )
    assert resp.status_code == 200
    
    # Verify acquisition_data was saved from URL params
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_url_utm@example.com"))
    assert user is not None
    assert user.acquisition_data is not None
    assert user.acquisition_data["utm_source"] == "google"
    assert user.acquisition_data["utm_medium"] == "cpc"
    assert user.acquisition_data["utm_campaign"] == "legisladores_2024"
    assert user.acquisition_data["utm_term"] == "software legislativo"  # Note: + is decoded to space
    assert "captured_at" in user.acquisition_data


def test_register_with_url_custom_params(client, db_session):
    """Test registration with custom params in URL query string"""
    payload = {
        "email": "test_url_custom@example.com",
        "password": "senha123",
        "first_name": "URLCustom",
        "permission_level": "User",
        "lgpd_check": True,
    }
    
    resp = client.post(
        "/auth/register?ref=parceiro_x&promo_code=DESCONTO20&source_page=landing",
        json=payload
    )
    assert resp.status_code == 200
    
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_url_custom@example.com"))
    assert user is not None
    assert user.acquisition_data is not None
    assert user.acquisition_data["ref"] == "parceiro_x"
    assert user.acquisition_data["promo_code"] == "DESCONTO20"
    assert user.acquisition_data["source_page"] == "landing"


def test_register_body_params_override_url_params(client, db_session):
    """Test that body JSON params take priority over URL params"""
    payload = {
        "email": "test_priority@example.com",
        "password": "senha123",
        "first_name": "Priority",
        "permission_level": "User",
        "lgpd_check": True,
        "query_params": {
            "utm_source": "facebook",  # Body says facebook
            "utm_campaign": "social_promo"
        }
    }
    
    # URL says google, but body should win
    resp = client.post(
        "/auth/register?utm_source=google&utm_medium=cpc",
        json=payload
    )
    assert resp.status_code == 200
    
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_priority@example.com"))
    assert user is not None
    assert user.acquisition_data is not None
    # Body param should override URL param
    assert user.acquisition_data["utm_source"] == "facebook"
    # Body-only param should be present
    assert user.acquisition_data["utm_campaign"] == "social_promo"
    # URL-only param should also be present
    assert user.acquisition_data["utm_medium"] == "cpc"


def test_register_url_and_body_params_merged(client, db_session):
    """Test that URL and body params are merged correctly"""
    payload = {
        "email": "test_merged@example.com",
        "password": "senha123",
        "first_name": "Merged",
        "permission_level": "User",
        "lgpd_check": True,
        "query_params": {
            "ref": "influencer_john",
            "device": "mobile"
        }
    }
    
    resp = client.post(
        "/auth/register?utm_source=instagram&utm_campaign=influencer_promo",
        json=payload
    )
    assert resp.status_code == 200
    
    user = db_session.scalar(select(UserORM).where(UserORM.email == "test_merged@example.com"))
    assert user is not None
    assert user.acquisition_data is not None
    # URL params
    assert user.acquisition_data["utm_source"] == "instagram"
    assert user.acquisition_data["utm_campaign"] == "influencer_promo"
    # Body params
    assert user.acquisition_data["ref"] == "influencer_john"
    assert user.acquisition_data["device"] == "mobile"
    assert "captured_at" in user.acquisition_data
