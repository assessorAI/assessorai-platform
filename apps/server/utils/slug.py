"""Slug generation utilities for mandato names."""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session


def _normalize(text: str) -> str:
    """Convert text to a URL-friendly slug base."""
    # Decompose accented characters then drop the combining marks
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower().strip()
    # Replace any run of non-alphanumeric chars with a single hyphen
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    # Strip leading/trailing hyphens
    return hyphenated.strip("-")


def generate_unique_slug(
    nome: Optional[str],
    session: Session,
    mandato_id: Optional[int] = None,
    fallback_id: Optional[int] = None,
) -> str:
    """Return a unique slug for a mandato.

    Args:
        nome: ``nome_parlamentar`` value.
        session: Active SQLAlchemy session used for uniqueness checks.
        mandato_id: When updating an existing mandato, pass its id so the
            current slug owner is excluded from the uniqueness check.
        fallback_id: Used to build ``mandato-{id}`` when nome is blank.

    Returns:
        A unique slug string.
    """
    # Import here to avoid circular imports at module load time
    from ..db.models import Mandato as MandatoORM  # noqa: PLC0415

    if nome and nome.strip():
        base = _normalize(nome)
    else:
        base = f"mandato-{fallback_id}" if fallback_id else "mandato"

    # Ensure the base is not empty after normalization
    if not base:
        base = f"mandato-{fallback_id}" if fallback_id else "mandato"

    candidate = base
    suffix = 2
    while True:
        stmt = select(MandatoORM).where(MandatoORM.slug == candidate)
        if mandato_id is not None:
            stmt = stmt.where(MandatoORM.id != mandato_id)
        existing = session.scalar(stmt)
        if existing is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1
