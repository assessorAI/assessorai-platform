from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import List


DEFAULT_MANDATO_CARGOS_FILE = Path(__file__).resolve().parents[1] / "config" / "mandato_cargos.json"


@lru_cache()
def load_mandato_cargos() -> List[str]:
    """Return the list of allowed mandato cargos from configuration."""
    config_path = Path(os.getenv("MANDATO_CARGOS_FILE", str(DEFAULT_MANDATO_CARGOS_FILE))).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Mandato cargos configuration not found at {config_path}")
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    cargos = raw.get("mandato_cargos")
    if not isinstance(cargos, list) or not all(isinstance(item, str) for item in cargos):
        raise ValueError("mandato_cargos must be a list of strings")
    return cargos


def get_frontend_url() -> str:
    """Return the frontend URL from environment or default."""
    return os.getenv("FRONTEND_URL", "http://localhost:8000")
