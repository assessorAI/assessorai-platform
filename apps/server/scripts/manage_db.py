#!/usr/bin/env python3
"""Database management utility supporting incremental migrations and full rebuilds."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Set, Tuple

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.base import Base
import db.session as db_session

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("DB_REFRESH_LOG_LEVEL", "INFO"))

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "db" / "migrations"
DEFAULT_MODE = "incremental"
FULL_REBUILD_ALIASES = {"rebuild", "reset", "wipe", "full"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage database schema migrations.")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["incremental", "rebuild"],
        help="Migration mode. Overrides DB_REFRESH_MODE when provided.",
    )
    return parser.parse_args()


def resolve_mode(cli_mode: str | None) -> str:
    env_mode = os.getenv("DB_REFRESH_MODE", DEFAULT_MODE).strip().lower()

    if cli_mode:
        return cli_mode

    if env_mode in FULL_REBUILD_ALIASES:
        return "rebuild"
    if env_mode == "incremental":
        return "incremental"

    logger.warning(
        "Unknown DB_REFRESH_MODE='%s'. Defaulting to '%s'.", env_mode, DEFAULT_MODE
    )
    return DEFAULT_MODE


def ensure_schema_migrations_table(conn) -> None:
    """Ensure the schema_migrations bookkeeping table exists (PostgreSQL only)."""
    conn.exec_driver_sql(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename VARCHAR(255) PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """
    )


def ensure_pgvector_extension(conn) -> None:
    try:
        conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        logger.info("pgvector extension available.")
    except SQLAlchemyError as exc:
        logger.warning("Não foi possível habilitar a extensão pgvector automaticamente: %s", exc)


def fetch_applied_migrations(conn) -> set[str]:
    result = conn.execute(text("SELECT filename FROM schema_migrations"))
    return {row[0] for row in result}


def list_migration_files() -> List[Path]:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(path for path in MIGRATIONS_DIR.glob("*.sql") if path.is_file())


StatementSpec = Tuple[Optional[Set[str]], str]


def parse_sql_statements(sql_blob: str) -> List[StatementSpec]:
    """Split a SQL file into individual statements, capturing optional dialect filters.
    
    Handles dollar-quoted blocks (DO $$ ... END $$;) correctly.
    """
    statements: List[StatementSpec] = []
    buffer: List[str] = []
    target_dialects: Optional[Set[str]] = None
    in_dollar_quote = False

    for raw_line in sql_blob.splitlines():
        line = raw_line.strip()
        if line.lower().startswith("-- dialect:"):
            dialect_part = line.split(":", 1)[1]
            target_dialects = {
                part.strip().lower()
                for part in dialect_part.split(",")
                if part.strip()
            } or None
            continue
        if not line or line.startswith("--"):
            continue
        
        # Track dollar-quoted blocks
        if "$$" in line:
            in_dollar_quote = not in_dollar_quote
        
        buffer.append(raw_line)
        
        # Only split on semicolon if we're not inside a dollar-quoted block
        if line.endswith(";") and not in_dollar_quote:
            statement = "\n".join(buffer).strip()
            if statement.endswith(";"):
                statement = statement[:-1]
            if statement:
                statements.append((target_dialects, statement))
            buffer = []
            target_dialects = None

    if buffer:
        statement = "\n".join(buffer).strip()
        if statement:
            statements.append((target_dialects, statement))

    return statements


def apply_sql_file(conn, path: Path) -> None:
    sql_blob = path.read_text(encoding="utf-8")
    statements = parse_sql_statements(sql_blob)
    if not statements:
        logger.info("Skipping %s (no SQL statements detected).", path.name)
        return

    dialect_name = db_session.engine.dialect.name
    executed = 0
    for dialects, statement in statements:
        if dialects and dialect_name not in dialects:
            continue

        conn.exec_driver_sql(statement)
        executed += 1

    if executed:
        logger.info(
            "Applied migration %s (%s/%s statements executed for dialect=%s).",
            path.name,
            executed,
            len(statements),
            dialect_name,
        )
        conn.execute(
            text(
                "INSERT INTO schema_migrations (filename, applied_at) "
                "VALUES (:filename, CURRENT_TIMESTAMP)"
            ),
            {"filename": path.name},
        )
    else:
        logger.info(
            "No applicable statements in %s for dialect=%s; marking as applied.",
            path.name,
            dialect_name,
        )
        conn.execute(
            text(
                "INSERT INTO schema_migrations (filename, applied_at) "
                "VALUES (:filename, CURRENT_TIMESTAMP)"
            ),
            {"filename": path.name},
        )


def apply_migrations(conn, mode: str) -> None:
    ensure_schema_migrations_table(conn)
    already_applied = fetch_applied_migrations(conn)

    migration_files = list_migration_files()
    if not migration_files:
        logger.info("No SQL migrations found. Schema ensured via SQLAlchemy metadata.")
        return

    for path in migration_files:
        if mode == "incremental" and path.name in already_applied:
            continue
        apply_sql_file(conn, path)


def drop_all_schema(conn) -> None:
    logger.warning("Dropping all tables in public schema (CASCADE).")
    conn.exec_driver_sql("DROP SCHEMA IF EXISTS public CASCADE")
    conn.exec_driver_sql("CREATE SCHEMA public")


def ensure_user_activation_flag(conn) -> None:
    conn.exec_driver_sql(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
    )
    conn.exec_driver_sql("UPDATE users SET is_active = TRUE WHERE is_active IS NULL")


def main() -> None:
    args = parse_args()
    mode = resolve_mode(args.mode)
    logger.info("Running database manager in '%s' mode.", mode)

    # Ensure models are registered with metadata
    __import__("db.models")

    db_session.init_db()

    try:
        with db_session.engine.begin() as conn:
            if mode == "rebuild":
                drop_all_schema(conn)

            ensure_pgvector_extension(conn)

            logger.info("Ensuring tables from SQLAlchemy metadata are present.")
            Base.metadata.create_all(bind=conn)

            ensure_user_activation_flag(conn)
            apply_migrations(conn, mode)
    except SQLAlchemyError as exc:
        logger.exception("Database management failed: %s", exc)
        raise SystemExit(1) from exc
    except Exception as exc:
        logger.exception("Unexpected error during database management: %s", exc)
        raise SystemExit(1) from exc
    logger.info("Database management completed successfully.")


if __name__ == "__main__":
    main()
