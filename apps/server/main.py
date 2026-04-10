import os
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# Ensure the repository root is importable when running via `fastapi run main.py`.
PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Autenticação baseada em Bearer token no header
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .routers import (
    auth,
    oficios,
    expertPL,
    upload,
    vectorSearch,
    mandatos,
    users,
    validation,
    admin,
    vector_admin,
    audit as audit_router,
    prompts,
    prompt_evaluation,
    analytics,
    coleta_demandas,
    coleta_demandas_triagem,
)
from .db.session import init_db
from .routers.deps import get_current_user
from .services import audit

load_dotenv()

from .utils.google_creds import ensure_google_credentials_file  # crie este arquivo utilitário
ensure_google_credentials_file()

# Initialize rate limiter (disabled during tests to avoid rate limit errors)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    enabled=not bool(os.getenv("PYTEST_CURRENT_TEST"))
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup (skip in tests where migrations are run separately)
    if not os.getenv("PYTEST_CURRENT_TEST"):
        init_db()
    yield
    # Shutdown (if needed in the future)


app = FastAPI(
    title="API do Assessoraí",
    description="Ferramentas com IA para auxiliar no legislativo.",
    version="0.0.1",
    lifespan=lifespan,
)

# Configure logging level
logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG") == "True" else logging.INFO)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8501,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def audit_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or request.scope.get("trace_id")
    if not request_id:
        request_id = audit.get_request_id()
    audit.set_request_id(request_id)
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response



app.include_router(auth.router)
app.include_router(validation.router)
app.include_router(coleta_demandas.router)
app.include_router(coleta_demandas_triagem.router)

# Roteadores protegidos por bearer token
app.include_router(oficios.router, dependencies=[Depends(get_current_user)])
app.include_router(expertPL.router, dependencies=[Depends(get_current_user)])
app.include_router(upload.router, dependencies=[Depends(get_current_user)])
app.include_router(vectorSearch.router, dependencies=[Depends(get_current_user)])
app.include_router(mandatos.public_router)  # GET /mandatos/{id_ou_slug} — público
app.include_router(mandatos.router, dependencies=[Depends(get_current_user)])
# /user restricted to admin/manager
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(vector_admin.router)
app.include_router(audit_router.router)
app.include_router(prompts.router)
app.include_router(prompt_evaluation.router)
app.include_router(analytics.router)

@app.get("/test")
async def test():
    return {"status": "ok"}
