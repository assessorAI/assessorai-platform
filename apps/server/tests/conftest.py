import os
import subprocess
import time
import atexit
import psycopg2
import warnings

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# Set test database URL before any imports
os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5434/assessorai_test"
# Set PYTEST_CURRENT_TEST to disable rate limiting in tests
os.environ["PYTEST_CURRENT_TEST"] = "true"

from assessorai.services.embeddings import EmbeddingProvider, get_embedding_dimension
from assessorai.routers import deps as router_deps

# Increase token expiration for tests to avoid expiration during long runs
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "120"

# Set dummy Google credentials for tests only if not already configured
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.getenv("GOOGLE_APPLICATION_BASE64"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/tmp/dummy_google_creds.json"
    with open("/tmp/dummy_google_creds.json", "w") as f:
        f.write('{"type": "service_account", "dummy": true}')


def check_test_environment():
    """
    Check for optional external service configurations and warn user.
    Tests will run with mock/dummy services, but some integration tests may behave differently.
    """
    warnings_list = []
    
    # Check OpenAI configuration
    if not os.getenv("OPENAI_API_KEY"):
        warnings_list.append(
            "OPENAI_API_KEY not set - AI features will use mock embeddings. "
            "Some expert_pl and vector search tests may return simplified results."
        )
    
    # Check Google Cloud Storage configuration
    real_gcs_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not real_gcs_creds or real_gcs_creds == "/tmp/dummy_google_creds.json":
        warnings_list.append(
            "GOOGLE_APPLICATION_CREDENTIALS not set to real service account - "
            "File upload tests may fail or return 400/422. Set this to test full GCS integration."
        )
    
    if not os.getenv("GCS_BUCKET_NAME"):
        warnings_list.append(
            "GCS_BUCKET_NAME not set - File storage tests will fail. "
            "Set this variable to test full file upload/download workflows."
        )
    
    # Check SendGrid configuration (for email tests)
    if not os.getenv("SENDGRID_API_KEY"):
        warnings_list.append(
            "SENDGRID_API_KEY not set - Email notification tests will be skipped or mocked."
        )
    
    # Display warnings
    if warnings_list:
        warning_message = "\n\n" + "="*80 + "\n"
        warning_message += "  TEST ENVIRONMENT CONFIGURATION WARNINGS\n"
        warning_message += "="*80 + "\n\n"
        warning_message += "The following external services are not configured:\n\n"
        for i, warning in enumerate(warnings_list, 1):
            warning_message += f"{i}. {warning}\n\n"
        warning_message += "Tests will run with mock services where possible.\n"
        warning_message += "For full integration testing, see tests/README.md for setup instructions.\n"
        warning_message += "="*80 + "\n"
        warnings.warn(warning_message, UserWarning, stacklevel=2)


# Run environment check when tests start
check_test_environment()

def wait_for_db(host, port, dbname, user, password, timeout=30):
    """Wait for PostgreSQL to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            conn = psycopg2.connect(
                host=host, port=port, dbname=dbname, user=user, password=password
            )
            conn.close()
            return True
        except psycopg2.OperationalError:
            time.sleep(1)
    return False

@pytest.fixture(scope="session", autouse=True)
def test_db_container():
    """Start a temporary PostgreSQL container for tests using custom Dockerfile and clean it up after."""
    container_name = "assessorai-test-postgres"
    db_name = "assessorai_test"
    db_user = "test"
    db_password = "test"
    host_port = "5434"
    image_name = "assessorai-test-postgres"

    # Build the image from Dockerfile.postgres if not exists
    result = subprocess.run(
        ["docker", "images", "-q", image_name],
        capture_output=True, text=True
    )
    if not result.stdout.strip():
        # Build image
        subprocess.run([
            "docker", "build", "-t", image_name, "-f", "Dockerfile.postgres", "."
        ], check=True)

    # Check if container exists (even if stopped)
    result_exists = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={container_name}"],
        capture_output=True, text=True
    )
    container_exists = result_exists.returncode == 0 and result_exists.stdout.strip()

    if container_exists:
        # Check if container is running
        result_running = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_name}"],
            capture_output=True, text=True
        )
        if result_running.returncode == 0 and result_running.stdout.strip():
            pass  # Container is already running
        else:
            # Start the existing container
            subprocess.run(["docker", "start", container_name], check=True)
    else:
        # Container doesn't exist, create it
        subprocess.run([
            "docker", "run", "-d", "--name", container_name,
            "-e", f"POSTGRES_DB={db_name}",
            "-e", f"POSTGRES_USER={db_user}",
            "-e", f"POSTGRES_PASSWORD={db_password}",
            "-p", f"{host_port}:5432",
            image_name
        ], check=True)

    # Wait for DB readiness
    if not wait_for_db("localhost", host_port, db_name, db_user, db_password, timeout=60):
        raise RuntimeError("Database did not become ready in time")

    # Run migrations
    subprocess.run(["python3", "scripts/manage_db.py", "--mode", "rebuild"], check=True)

    import assessorai.db.session as session_module
    session_module.init_db()

    # Enable vector extension for tests before creating tables
    with session_module.engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    dim = get_embedding_dimension()

    class DummyEmbeddingProvider(EmbeddingProvider):
        name = "test-double"

        def embed(self, texts):
            return [[float(idx + 1)] * dim for idx, _ in enumerate(texts)]

    from assessorai.main import app
    app.dependency_overrides[router_deps.get_embedding_provider_dep] = lambda: DummyEmbeddingProvider()
    return app


@pytest.fixture()
def client():
    from assessorai.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    """Provide a direct database session for tests."""
    import assessorai.db.session as db_session_module
    from assessorai.db.base import Base

    table_names = [table.name for table in Base.metadata.sorted_tables]
    if table_names:
        truncate_sql = (
            "TRUNCATE TABLE "
            + ", ".join(f'"{name}"' for name in table_names)
            + " RESTART IDENTITY CASCADE"
        )
        with db_session_module.engine.begin() as conn:
            conn.execute(text(truncate_sql))

    session = db_session_module.SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def admin_user(client, db_session):
    """Create and return an admin user ORM object."""
    from assessorai.db.models import User as UserORM
    from sqlalchemy import select
    
    # Check if user already exists
    existing = db_session.scalar(select(UserORM).where(UserORM.email == "admin@example.com"))
    if existing:
        return existing
    
    # Create admin user via registration
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
    
    # Fetch and return the user object
    user = db_session.scalar(select(UserORM).where(UserORM.email == "admin@example.com"))
    return user


@pytest.fixture()
def manager_token(client, db_session):
    """Create a manager user and return authentication token."""
    from assessorai.db.models import User as UserORM
    from sqlalchemy import select
    
    # Check if manager exists
    existing = db_session.scalar(select(UserORM).where(UserORM.email == "manager@example.com"))
    if not existing:
        # Create manager user via registration
        payload = {
            "email": "manager@example.com",
            "first_name": "Manager",
            "last_name": "User",
            "phone": "(11) 88888-8888",
            "permission_level": "Manager",
            "lgpd_check": True,
            "role": "manager",
            "password": "manager123",
            "mandato": [
                {
                    "nome_parlamentar": "Manager User",
                    "casa_legislativa": "Câmara Municipal",
                    "cargo_parlamentar": "Vereador",
                    "municipio": "São Paulo",
                    "ue": "SP",
                }
            ],
        }
        client.post("/auth/register", json=payload)
    
    # Get token
    token_response = client.post(
        "/auth/token",
        data={"username": "manager@example.com", "password": "manager123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    return token_response.json()["access_token"]


@pytest.fixture()
def auth_headers(client):
    # Create an admin user and return Bearer token headers
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
    r = client.post("/auth/register", json=payload)
    assert r.status_code in (200, 400)  # may already exist if reused in session
    token = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def user_headers(client):
    """Create a regular user (User permission) and return Bearer token headers"""
    payload = {
        "email": "user@example.com",
        "first_name": "Regular",
        "last_name": "User",
        "phone": "(11) 77777-7777",
        "permission_level": "User",
        "lgpd_check": True,
        "role": "assessor",
        "password": "user123",
        "mandato": [
            {
                "nome_parlamentar": "Regular User",
                "casa_legislativa": "Câmara Municipal",
                "cargo_parlamentar": "Vereador",
                "municipio": "Rio de Janeiro",
                "ue": "RJ",
            }
        ],
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code in (200, 400)  # may already exist if reused in session
    token = client.post(
        "/auth/token",
        data={"username": payload["email"], "password": payload["password"]},
        headers={"content-type": "application/x-www-form-urlencoded"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
