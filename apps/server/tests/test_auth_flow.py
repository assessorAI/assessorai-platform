from datetime import datetime, timedelta, timezone
import secrets
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from assessorai.db.models import User as UserORM, PasswordResetToken as PasswordResetTokenORM, UserActivationToken as UserActivationTokenORM, Mandato as MandatoORM
from assessorai.models import PermissionLevel
from assessorai.utils.security import get_password_hash

def test_register_and_login_and_me(client: TestClient):
    # register
    payload = {
        "email": "user1@example.com",
        "first_name": "User",
        "last_name": "One",
        "phone": "(11) 99999-9999",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "member",
        "password": "secret123",
        "mandato": [
            {
                "nome_parlamentar": "User One",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "São Paulo",
                "ue": "SP",
            }
        ],
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 200 or r.status_code == 400
    if r.status_code == 200:
        body = r.json()
        assert isinstance(body.get("mandato"), list)
        assert body["mandato"], "registro deve retornar mandato criado"

    # login
    r2 = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert r2.status_code == 200
    token = r2.json()["access_token"]

    # me
    r3 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    body = r3.json()
    assert body["email"] == payload["email"]
    assert body["cargo_parlamentar"] == payload["mandato"][0]["cargo_parlamentar"]
    assert isinstance(body.get("mandato"), list)
    assert body["mandato"], "/auth/me deve retornar mandatos do usuário"


def test_login_wrong_password(client: TestClient):
    """Testa falha de login com senha errada."""
    payload = {
        "email": "user2@example.com",
        "first_name": "User",
        "last_name": "Two",
        "phone": "(11) 99999-9999",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "member",
        "password": "secret123",
        "mandato": [
            {
                "nome_parlamentar": "User Two",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "São Paulo",
                "ue": "SP",
            }
        ],
    }
    client.post("/auth/register", json=payload)

    r = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": "wrongpassword"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 401


def test_register_duplicate_email(client: TestClient):
    """Testa erro ao registrar email duplicado."""
    payload = {
        "email": "duplicate@example.com",
        "first_name": "Duplicate",
        "last_name": "User",
        "phone": "(11) 99999-9999",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "member",
        "password": "secret123",
        "mandato": [],
    }
    client.post("/auth/register", json=payload)
    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400


def create_test_user_for_reset(client, email: str = "reset@example.com"):
    """Helper para criar usuário de teste."""
    payload = {
        "email": email,
        "first_name": "Reset",
        "last_name": "User",
        "phone": "(11) 98888-8888",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "tester",
        "password": "password123",
        "mandato": []
    }
    response = client.post("/auth/register", json=payload)
    return response


def test_forgot_password_existing_email(client):
    """Testa solicitação de recuperação para e-mail existente."""
    create_test_user_for_reset(client, "reset1@example.com")

    response = client.post(
        "/auth/forgot-password",
        json={"email": "reset1@example.com"}
    )

    assert response.status_code == 200
    assert "receberá instruções" in response.json()["message"]


def test_forgot_password_nonexistent_email(client):
    """Testa solicitação de recuperação para e-mail inexistente (mesma resposta por segurança)."""
    response = client.post(
        "/auth/forgot-password",
        json={"email": "nonexistent@example.com"}
    )

    assert response.status_code == 200
    assert "receberá instruções" in response.json()["message"]


def test_forgot_password_invalid_email(client):
    """Testa solicitação com e-mail inválido."""
    response = client.post(
        "/auth/forgot-password",
        json={"email": "invalid-email"}
    )

    assert response.status_code == 422  # Validation error


def test_reset_password_valid_token(client, db_session, admin_user):
    """Testa redefinição de senha com token válido."""
    from datetime import datetime, timedelta, timezone
    from db.models import PasswordResetToken as PasswordResetTokenORM
    import secrets
    
    # Cria token válido diretamente no banco
    token_string = secrets.token_urlsafe(32)
    reset_token = PasswordResetTokenORM(
        token=token_string,
        user_id=admin_user.id,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
        used=False
    )
    db_session.add(reset_token)
    db_session.commit()
    
    # Tenta redefinir senha com o token válido
    response = client.post(
        "/auth/reset-password",
        json={
            "token": token_string,
            "new_password": "NewSecurePass123!"
        }
    )
    
    assert response.status_code == 200
    assert "sucesso" in response.json()["message"].lower()
    
    # Verifica que o token foi marcado como usado
    db_session.refresh(reset_token)
    assert reset_token.used is True


def test_reset_password_invalid_token(client):
    """Testa redefinição com token inválido."""
    response = client.post(
        "/auth/reset-password",
        json={
            "token": "a" * 43,  # Token com tamanho válido mas inexistente
            "new_password": "newPassword123"
        }
    )

    assert response.status_code == 400
    assert "inválido ou expirado" in response.json()["detail"]


def test_reset_password_expired_token(client, db_session, admin_user):
    """Testa redefinição com token expirado."""
    from datetime import datetime, timedelta, timezone
    from db.models import PasswordResetToken as PasswordResetTokenORM
    import secrets
    
    # Cria token expirado (1 hora no passado)
    token_string = secrets.token_urlsafe(32)
    expired_token = PasswordResetTokenORM(
        token=token_string,
        user_id=admin_user.id,
        expires_at=(datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None),
        used=False
    )
    db_session.add(expired_token)
    db_session.commit()
    
    # Tenta redefinir senha com token expirado
    response = client.post(
        "/auth/reset-password",
        json={
            "token": token_string,
            "new_password": "NewSecurePass123!"
        }
    )
    
    assert response.status_code == 400
    assert "expirado" in response.json()["detail"].lower()


def test_reset_password_used_token(client, db_session, admin_user):
    """Testa redefinição com token já utilizado."""
    from datetime import datetime, timedelta, timezone
    from db.models import PasswordResetToken as PasswordResetTokenORM
    import secrets
    
    # Cria token válido mas já usado
    token_string = secrets.token_urlsafe(32)
    used_token = PasswordResetTokenORM(
        token=token_string,
        user_id=admin_user.id,
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None),
        used=True  # Marca como já utilizado
    )
    db_session.add(used_token)
    db_session.commit()
    
    # Tenta redefinir senha com token já usado
    response = client.post(
        "/auth/reset-password",
        json={
            "token": token_string,
            "new_password": "NewSecurePass123!"
        }
    )
    
    assert response.status_code == 400
    assert "já foi utilizado" in response.json()["detail"]


def test_reset_password_short_password(client):
    """Testa redefinição com senha muito curta."""
    response = client.post(
        "/auth/reset-password",
        json={
            "token": "a" * 43,
            "new_password": "short"  # Menos de 8 caracteres
        }
    )

    assert response.status_code == 422  # Validation error


def test_manager_adds_new_user_creates_inactive_user(client: TestClient, db_session, manager_token):
    """
    Testa que quando o manager adiciona um novo usuário (que não existe),
    o sistema cria um usuário inativo com permission_level='invited'
    """
    # Cria um mandato
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    db_session.add(mandato)
    db_session.commit()

    # Manager adiciona novo usuário ao mandato
    response = client.post(
        f"/mandatos/{mandato.id}/users",
        json={"email": "newuser@example.com"},
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200

    # Verifica que o usuário foi criado como inativo
    user = db_session.scalar(select(UserORM).where(UserORM.email == "newuser@example.com"))
    assert user is not None
    assert user.is_active == False
    assert user.permission_level == PermissionLevel.invited.value
    assert user.first_name is None
    assert user.last_name is None
    assert user.phone is None

    # Verifica que o token de ativação foi criado
    token = db_session.scalar(select(UserActivationTokenORM).where(UserActivationTokenORM.user_id == user.id))
    assert token is not None
    assert token.mandato_id == mandato.id
    assert token.used == False
    assert token.expires_at > datetime.now(timezone.utc).replace(tzinfo=None)


def test_manager_adds_existing_user_just_adds_to_mandato(client: TestClient, db_session, manager_token, admin_user):
    """
    Testa que quando o manager adiciona um usuário existente,
    o sistema apenas adiciona o usuário ao mandato (sem criar novo token)
    """
    # Cria um mandato
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    db_session.add(mandato)
    db_session.commit()

    # Manager adiciona usuário existente ao mandato
    response = client.post(
        f"/mandatos/{mandato.id}/users",
        json={"email": admin_user.email},
        headers={"Authorization": f"Bearer {manager_token}"}
    )

    assert response.status_code == 200

    # Verifica que não foi criado token de ativação
    tokens = db_session.scalars(select(UserActivationTokenORM).where(UserActivationTokenORM.user_id == admin_user.id)).all()
    assert len(tokens) == 0


def test_get_activate_with_valid_token_returns_email(client: TestClient, db_session):
    """
    Testa que GET /auth/activate com token válido retorna o email do usuário
    """
    # Cria usuário inativo
    user = UserORM(
        email="invited@example.com",
        permission_level=PermissionLevel.invited.value,
        is_active=False,
        hashed_password="temppassword"
    )
    db_session.add(user)

    # Cria mandato
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    db_session.add(mandato)
    db_session.flush()

    # Cria token de ativação
    token_str = secrets.token_urlsafe(32)
    token = UserActivationTokenORM(
        token=token_str,
        user_id=user.id,
        mandato_id=mandato.id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
        used=False
    )
    db_session.add(token)
    db_session.commit()

    # Verifica token
    response = client.get(f"/auth/activate?token={token_str}")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "invited@example.com"
    assert data["mandato_nome"] == "Test Mandato"


def test_get_activate_with_invalid_token_fails(client: TestClient):
    """
    Testa que GET /auth/activate com token inválido retorna erro
    """
    response = client.get("/auth/activate?token=invalidtoken123456")

    assert response.status_code == 400
    assert "inválido" in response.json()["detail"].lower()


def test_get_activate_with_expired_token_fails(client: TestClient, db_session):
    """
    Testa que GET /auth/activate com token expirado retorna erro
    """
    # Cria usuário inativo
    user = UserORM(
        email="invited@example.com",
        permission_level=PermissionLevel.invited.value,
        is_active=False,
        hashed_password="temppassword"
    )
    db_session.add(user)

    # Cria mandato
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    db_session.add(mandato)
    db_session.flush()

    # Cria token expirado
    token_str = secrets.token_urlsafe(32)
    token = UserActivationTokenORM(
        token=token_str,
        user_id=user.id,
        mandato_id=mandato.id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
        used=False
    )
    db_session.add(token)
    db_session.commit()

    # Verifica token
    response = client.get(f"/auth/activate?token={token_str}")

    assert response.status_code == 400
    assert "expirado" in response.json()["detail"].lower()


def test_get_activate_with_used_token_fails(client: TestClient, db_session):
    """
    Testa que GET /auth/activate com token já usado retorna erro
    """
    # Cria usuário inativo
    user = UserORM(
        email="invited@example.com",
        permission_level=PermissionLevel.invited.value,
        is_active=False,
        hashed_password="temppassword"
    )
    db_session.add(user)

    # Cria mandato
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    db_session.add(mandato)
    db_session.flush()

    # Cria token usado
    token_str = secrets.token_urlsafe(32)
    token = UserActivationTokenORM(
        token=token_str,
        user_id=user.id,
        mandato_id=mandato.id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
        used=True  # Já usado
    )
    db_session.add(token)
    db_session.commit()

    # Verifica token
    response = client.get(f"/auth/activate?token={token_str}")

    assert response.status_code == 400
    assert "utilizado" in response.json()["detail"].lower()


def test_post_activate_completes_user_registration(client: TestClient, db_session):
    """
    Testa que POST /auth/activate completa o cadastro do usuário
    """
    # Cria usuário inativo
    user = UserORM(
        email="invited@example.com",
        permission_level=PermissionLevel.invited.value,
        is_active=False,
        hashed_password="temppassword",
        lgpd_check=False
    )
    db_session.add(user)

    # Cria mandato
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    db_session.add(mandato)
    db_session.flush()

    # Cria token de ativação
    token_str = secrets.token_urlsafe(32)
    token = UserActivationTokenORM(
        token=token_str,
        user_id=user.id,
        mandato_id=mandato.id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
        used=False
    )
    db_session.add(token)
    db_session.commit()

    # Ativa o usuário
    response = client.post("/auth/activate", json={
        "token": token_str,
        "first_name": "John",
        "last_name": "Doe",
        "phone": "(11) 99999-9999",
        "password": "SecurePass123",
        "lgpd_check": True,
        "role": "Assessor"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "invited@example.com"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"

    # Verifica que o usuário foi atualizado no banco
    db_session.refresh(user)
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.phone == "(11) 99999-9999"
    assert user.role == "Assessor"
    assert user.lgpd_check == True
    assert user.is_active == True
    assert user.permission_level == PermissionLevel.user.value

    # Verifica que o token foi marcado como usado
    db_session.refresh(token)
    assert token.used == True


def test_login_fails_for_inactive_user(client: TestClient, db_session):
    """
    Testa que usuário inativo não consegue fazer login
    """
    # Cria usuário inativo
    from assessorai.utils.security import get_password_hash
    user = UserORM(
        email="inactive@example.com",
        first_name="Inactive",
        last_name="User",
        phone="(11) 99999-9999",
        permission_level=PermissionLevel.invited.value,
        lgpd_check=False,
        role="Assessor",
        is_active=False,
        hashed_password=get_password_hash("password123")
    )
    db_session.add(user)
    db_session.commit()

    # Tenta fazer login
    response = client.post("/auth/token", data={
        "username": "inactive@example.com",
        "password": "password123"
    })

    assert response.status_code == 401


def test_login_succeeds_for_activated_user(client: TestClient, db_session):
    """
    Testa que usuário ativo consegue fazer login após ativação
    """
    # Cria usuário ativo
    from assessorai.utils.security import get_password_hash
    user = UserORM(
        email="active@example.com",
        first_name="Active",
        last_name="User",
        phone="(11) 99999-9999",
        permission_level=PermissionLevel.user.value,
        lgpd_check=True,
        role="Assessor",
        is_active=True,
        hashed_password=get_password_hash("password123")
    )
    db_session.add(user)

    # Cria mandato e associa
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    mandato.users.append(user)
    db_session.add(mandato)
    db_session.commit()

    # Faz login
    response = client.post("/auth/token", data={
        "username": "active@example.com",
        "password": "password123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_post_activate_with_invalid_token_fails(client: TestClient):
    """
    Testa que POST /auth/activate com token inválido retorna erro
    """
    response = client.post("/auth/activate", json={
        "token": "invalidtoken123456",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "(11) 99999-9999",
        "password": "SecurePass123",
        "lgpd_check": True,
        "role": "Assessor"
    })

    assert response.status_code == 422  # Pydantic validation error for invalid token format


def test_post_activate_enforces_single_use_token(client: TestClient, db_session):
    """
    Testa que o token de ativação só pode ser usado uma vez
    """
    # Cria usuário inativo
    user = UserORM(
        email="invited@example.com",
        permission_level=PermissionLevel.invited.value,
        is_active=False,
        hashed_password="temppassword",
        lgpd_check=False
    )
    db_session.add(user)

    # Cria mandato
    mandato = MandatoORM(nome_parlamentar="Test Mandato", cargo_parlamentar="Vereador")
    db_session.add(mandato)
    db_session.flush()

    # Cria token de ativação
    token_str = secrets.token_urlsafe(32)
    token = UserActivationTokenORM(
        token=token_str,
        user_id=user.id,
        mandato_id=mandato.id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7),
        used=False
    )
    db_session.add(token)
    db_session.commit()

    activation_data = {
        "token": token_str,
        "first_name": "John",
        "last_name": "Doe",
        "phone": "(11) 99999-9999",
        "password": "SecurePass123",
        "lgpd_check": True,
        "role": "Assessor"
    }

    # Primeira ativação: sucesso
    response = client.post("/auth/activate", json=activation_data)
    assert response.status_code == 200

    # Segunda ativação com o mesmo token: falha
    response = client.post("/auth/activate", json=activation_data)
    assert response.status_code == 400
    assert "utilizado" in response.json()["detail"].lower()
