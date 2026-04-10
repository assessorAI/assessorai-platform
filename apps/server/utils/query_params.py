from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func


def parse_csv_param(raw: Optional[str]) -> List[str]:
    """Parse a comma-separated query param into trimmed values.

    - Trims whitespace
    - Drops empty entries
    - Preserves order
    """

    if not raw:
        return []
    parts = [p.strip() for p in str(raw).split(",")]
    return [p for p in parts if p]


def ci_in(col, raw: Optional[str]):
    """Case-insensitive IN() filter for a CSV query param.

    Returns a SQLAlchemy clause or None when raw has no values.
    """

    values = parse_csv_param(raw)
    if not values:
        return None
    lowered: List[str] = []
    seen = set()
    for v in values:
        lv = v.lower()
        if lv in seen:
            continue
        seen.add(lv)
        lowered.append(lv)
    return func.lower(func.coalesce(col, "")).in_(lowered)
