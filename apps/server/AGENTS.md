# Agent Guidelines for AssessorAI

## Project Structure & Module Organization
The FastAPI backend boots via `app.py`, with routing and startup logic centralized in `main.py`. Domain routers live in `routers/`, sharing SQLAlchemy setup from `db/` and Pydantic helpers in `models.py`. Prompt assets sit in `prompts/`, document templates in `templates/`, utilities (including Google credential checks) in `utils/`, and the Streamlit console under `client/` with pages in `client/pages/`. Tests mirror these domains in `tests/` using fixtures from `tests/conftest.py`.

## Database Refresh Workflow
- Every deployment runs `/app/scripts/manage_db.py` before the API boots. This script applies SQL migrations from `db/migrations` against the database defined by `DATABASE_URL` (defaults to the local `assessorai.db` SQLite file).
- Deployment mode is controlled with the `DB_REFRESH_MODE` environment variable:
  - `incremental` *(default)*: apply only pending migrations.
  - `rebuild`, `full`, or `wipe`: drop every table and reapply all migrations from scratch.
- Railway (and any other container runtime) should set `DB_REFRESH_MODE` to the desired strategy in the build/deploy settings. Leaving it unset keeps incremental updates; temporarily switch to `rebuild` when a clean slate is required.
- Do not override the Docker start command on Railway—let the bundled `scripts/entrypoint.sh` run so migrations execute before the service comes online. Use Railway's deploy variables to flip `DB_REFRESH_MODE` instead of custom shell commands.
- Local developers can mirror the behaviour via the CLI:
  ```bash
  python scripts/manage_db.py --mode incremental   # apply new migrations
  python scripts/manage_db.py --mode rebuild       # wipe and rebuild
  ```
- When changing the schema:
  1. Add a new, sequentially numbered SQL file to `db/migrations` (e.g. `002_add_goal_status.sql`).
  2. Test locally with `python scripts/manage_db.py --mode incremental`.
  3. Commit the migration so every environment (including Railway) stays in sync.
- Prefer idempotent SQL in migrations whenever possible (`IF NOT EXISTS` for indexes/tables and additive alters) to avoid Railway incremental deploy failures when objects already exist.
- Before merging long-lived branches, confirm migration numbering does not collide (renumber if needed so each filename is unique and sequential).
- The Docker entrypoint `scripts/entrypoint.sh` enforces this workflow, guaranteeing the database is in the expected state before the API becomes available. Avoid bypassing this script on deploys.

## Admin Console Workflow
- The admin console is divided into pages (`2_📊_Admin_Dashboard.py`, `3_👥_Admin_Usuarios.py`, `4_🏛️_Admin_Mandatos.py`, `5_🩺_Admin_Health.py`, `6_📄_Admin_Oficios.py`, `7_🧠_Admin_Expert_PL.py`, `8_🔎_Admin_Busca_Referencias.py`, `9_📝_Admin_Auditoria.py`). Shared helpers are in `client/admin/`.
- Authentication happens on `client/app.py` via `/auth/token`. Only users with `permission_level="Admin"` gain access; the API enforces the same guard through `require_admin_user`.
- Set the backend endpoint with the environment variable `ASSESSORAI_API_URL` (defaults to `http://localhost:8000`). All Streamlit pages consume the REST endpoints; no direct database reads.
- Ensure Google credentials are provided via `GOOGLE_APPLICATION_BASE64` (preferred) or `GOOGLE_APPLICATION_CREDENTIALS` before running the API locally or in tests; the health page highlights any missing credentials.

## Build/Test Commands
- Ambiente local roda em NixOS: sempre entrar via `nix develop` antes de executar API/testes/scripts.
- Se alguma nova dependência de sistema/toolchain for necessária, atualizar `flake.nix` e validar novamente com `nix develop`.
- A suíte de testes usa PostgreSQL via Docker no `tests/conftest.py`; garanta `docker` disponível no host antes de rodar `pytest`.
- `uv venv .venv && source .venv/bin/activate`: create a local virtualenv.
- `uv pip install -e ".[client,test]"`: install backend/client/test dependencies in editable mode.
- `uvicorn main:app --reload`: run the API with live reload; `python app.py` respects the `DEBUG` flag.
- `streamlit run client/app.py`: open the operator console once the API responds.
- `pytest -q`: execute the automated tests; drop `-q` for verbose logs.
- **Install**: `pip install -e .`
- **Run API**: `DEBUG=True python3 app.py` (use this instead of uvicorn directly to handle relative imports correctly)
- **Run tests**: `pytest -q`
- **Run single test**: `pytest tests/test_users.py::test_users_crud -v`
- **Run test file**: `pytest tests/test_users.py -v`
- **Run with coverage**: `pytest --cov=.`

## Test User Credentials
For manual testing and automated scripts, use the default admin account:
- **Email**: `admin@example.com`
- **Password**: `admin123`
- **Permission Level**: Admin

This account is created by `scripts/create_admin.py` during initial setup and has full administrative access to all endpoints.

## Code Style Guidelines
- **Formatting**: PEP 8, 4-space indentation, 88 char line length
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants
- **Imports**: Standard library first, then third-party, then local (alphabetical within groups)
- **Types**: Use type hints for all function parameters and return values
- **Error handling**: Raise `HTTPException` for API errors, use descriptive messages
- **Models**: Extend Pydantic models from `models.py`, use `Field()` for validation
- **Security**: Load secrets via `os.getenv()`, never hardcode credentials
- **Comments**: Brief comments for non-obvious logic only, no docstrings required
- **Enums**: Use enums for repeated string literals
- **Database**: Use SQLAlchemy ORM, commit transactions explicitly
Follow PEP 8 with four-space indentation and descriptive `snake_case`. Group related endpoints inside existing router modules and keep path prefixes aligned with their filenames. Extend the shared Pydantic models in `models.py` so new payloads inherit validation metadata, and prefer enums for repeated literals. Load secrets via `os.getenv`, annotate public functions, and document non-obvious logic with short comments.

## Testing Guidelines
Add tests under `tests/` using the `test_<domain>.py` pattern so they run automatically. Reuse fixtures from `tests/conftest.py`, which provide a FastAPI `TestClient` and isolated PostgreSQL database (containerized for tests). Cover success and validation failure cases when touching dependencies in `routers/deps.py`, and run `pytest -q` before publishing changes. Narrow debugging with commands like `pytest tests/test_users.py -k create_user`.

## Git Workflow & Branch Strategy
**CRITICAL: Always follow this branching workflow:**

1. **Development Branch: `dev` (formerly `v2`)**
   - ALL development work happens here first
   - Create feature branches from `dev` if needed
   - Commit and test locally before pushing to `dev`
   - Run `pytest -q` to ensure all tests pass

2. **Staging Branch: `staging`**
   - Merge `dev` → `staging` when ready for staging deployment
   - Deploy to Railway staging environment for testing
   - **NEVER merge to production without staging validation**

3. **Production Branch: `production`**
   - Merge `staging` → `production` only after user confirms staging tests passed
   - **ALWAYS ask: "Did you test this in staging?"** before merging to production
   - Production deploys go to Railway production environment

**Workflow Example:**
```bash
# 1. Develop in dev branch
git checkout dev
# ... make changes, commit ...
git push origin dev

# 2. Deploy to staging
git checkout staging
git merge dev
git push origin staging
# Railway auto-deploys staging

# 3. User tests in staging, confirms it works

# 4. Deploy to production (only after user confirmation)
git checkout production
git merge staging
git push origin production
```

**Branch Protection Rules:**
- ❌ NEVER commit directly to `production`
- ❌ NEVER merge `dev` → `production` (must go through `staging`)
- ✅ ALWAYS ask user to test in staging before production merge
- ✅ ALWAYS run tests before pushing to any branch

## Commit & Pull Request Guidelines
Commit messages follow the conventional-commit prefix (`feat:`, `fix:`, `chore:`); keep subjects imperative and scoped. Each commit should preserve a running API. Pull requests need a concise summary, links to any tickets, and proof of tests (`pytest -q` output or Streamlit screenshots). Call out configuration or environment updates so reviewers can mirror the setup.

## Environment & Secrets
Store runtime settings in `.env` (e.g., `GOOGLE_APPLICATION_CREDENTIALS`, `GCS_BUCKET_NAME`, `DATABASE_URL`, `SQL_ECHO`) and load them via `python-dotenv`. Keep credential files such as `google-key.json` outside version control and reference them with the helper in `utils/google_creds.py`. The bundled `assessorai.db` supports local work, but confirm connection strings before deploying to Fly.io or another target. For embeddings, configure OpenAI via `OPENAI_API_KEY` (along with `OPENAI_EMBEDDING_MODEL`, `OPENAI_API_BASE`, `VECTOR_SEARCH_PROBES`, `EMBEDDING_BATCH_REQUEST`, `VECTOR_IMPORT_BATCH_SIZE` as needed).

## Working Rhythm
- After each work cycle, append a brief block to `HISTORY.md` summarizing what was tackled or left in progress. Use the current UTC timestamp as the block heading so it's easy to revisit open threads later.
