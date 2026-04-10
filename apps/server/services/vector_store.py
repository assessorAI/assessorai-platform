from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from time import perf_counter, time
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from ..db.models import ProjetoReferencia

logger = logging.getLogger(__name__)

# Cache for stats() with configurable TTL
_stats_cache: Dict[str, Any] = {"data": None, "timestamp": 0.0}


def _get_stats_cache_ttl() -> float:
    """Get stats cache TTL from environment or use default (5 minutes)."""
    raw_value = os.getenv("VECTOR_STATS_CACHE_TTL")
    if raw_value is None:
        return 300.0
    try:
        value = float(raw_value)
        return value if value > 0 else 300.0
    except ValueError:
        return 300.0


def invalidate_stats_cache() -> None:
    """Invalidate the stats cache. Call this after bulk operations."""
    global _stats_cache
    _stats_cache["data"] = None
    _stats_cache["timestamp"] = 0.0


@dataclass
class VectorDocument:
    title: Optional[str]
    house: Optional[str]
    type: Optional[str]
    number: Optional[int]
    presentation_date: Optional[str]
    year: Optional[int]
    author: Optional[List[str]]
    subject: Optional[str]
    full_text: Optional[str]
    chunk_text: str
    chunk_number: int
    length: Optional[int]
    url: Optional[str]
    scraped_at: Optional[str]
    metadata: Optional[Dict[str, Any]]
    embedding: List[float]


class VectorStorePgVector:
    """Persistence helper backed by pgvector-enabled PostgreSQL."""

    def __init__(self, session: Session):
        self.session = session

    def truncate(self) -> None:
        self.session.execute(text("TRUNCATE TABLE projetos_referencias RESTART IDENTITY"))
        self.session.commit()
        invalidate_stats_cache()

    def bulk_insert(self, documents: Iterable[VectorDocument]) -> int:
        payload = [
            {
                "title": doc.title,
                "house": doc.house,
                "type": doc.type,
                "number": doc.number,
                "presentation_date": doc.presentation_date,
                "year": doc.year,
                "author": doc.author,
                "subject": doc.subject,
                "full_text": doc.full_text,
                "chunk_text": doc.chunk_text,
                "chunk_number": doc.chunk_number,
                "length": doc.length,
                "url": doc.url,
                "scraped_at": doc.scraped_at,
                "metadata_json": doc.metadata,
                "embedding": doc.embedding,
            }
            for doc in documents
        ]
        if not payload:
            return 0
        
        # Chunk insertions to prevent PostgreSQL OOM with large batches
        # Each embedding is ~6KB, so 200 docs ≈ 1.2MB per SQL query (safe for PostgreSQL)
        try:
            chunk_size = max(1, int(os.getenv("VECTOR_BATCH_SIZE", "200")))
        except ValueError:
            chunk_size = 200
        
        total_inserted = 0
        for i in range(0, len(payload), chunk_size):
            chunk = payload[i : i + chunk_size]
            self.session.bulk_insert_mappings(ProjetoReferencia, chunk)
            self.session.commit()
            total_inserted += len(chunk)
            if len(payload) > chunk_size:
                logger.info(
                    f"bulk_insert: inserted chunk {i // chunk_size + 1} "
                    f"({len(chunk)} docs, {total_inserted}/{len(payload)} total)"
                )
        
        invalidate_stats_cache()
        return total_inserted

    def _resolve_probes(self) -> int:
        raw_value = os.getenv("VECTOR_SEARCH_PROBES")
        if raw_value is None:
            return 50
        try:
            value = int(raw_value)
        except ValueError:
            return 50
        return value if value > 0 else 50

    def search(
        self,
        embedding: List[float],
        *,
        limit: int,
        offset: int = 0,
        return_latency: bool = False,
        detail: bool = False,
        deduplicate: bool = True,
    ) -> List[Dict[str, Any]] | tuple[List[Dict[str, Any]], float]:
        probes = self._resolve_probes()
        if probes:
            self.session.execute(text("SET LOCAL ivfflat.probes = :probes"), {"probes": probes})
        query = (
            text(
                """
                SELECT
                    pr.id,
                    pr.title,
                    pr.house,
                    pr.type,
                    pr.number,
                    pr.presentation_date,
                    pr.year,
                    pr.author,
                    pr.subject,
                    (
                        SELECT pr0.full_text
                        FROM projetos_referencias pr0
                        WHERE COALESCE(pr0.title, '') = COALESCE(pr.title, '')
                          AND COALESCE(pr0.type, '') = COALESCE(pr.type, '')
                          AND COALESCE(pr0.house, '') = COALESCE(pr.house, '')
                          AND COALESCE(pr0.number, 0) = COALESCE(pr.number, 0)
                          AND COALESCE(pr0.year, 0) = COALESCE(pr.year, 0)
                          AND pr0.chunk_number = 0
                          AND pr0.full_text IS NOT NULL
                        ORDER BY pr0.id DESC
                        LIMIT 1
                    ) AS full_text,
                    pr.chunk_text,
                    pr.chunk_number,
                    pr.length,
                    pr.url,
                    pr.scraped_at,
                    pr.metadata_json AS metadata,
                    1 - (pr.embedding <=> :embedding) AS score
                FROM projetos_referencias pr
                ORDER BY pr.embedding <=> :embedding
                LIMIT :limit OFFSET :offset
                """
            ).bindparams(
                bindparam(
                    "embedding",
                    type_=ProjetoReferencia.__table__.c.embedding.type,
                )
            )
        )
        start = perf_counter()
        rows = self.session.execute(
            query,
            {"embedding": list(embedding), "limit": limit, "offset": offset},
        ).mappings()
        if not deduplicate:
            results: List[Dict[str, Any]] = []
            for row in rows:
                payload = dict(row)
                # HACKISH: Renaming full_text to chunk_text in output for API compatibility
                # TODO: Standardize field naming across database schema and API responses
                if "full_text" in payload:
                    payload["chunk_text"] = payload.pop("full_text")
                if payload.get("score") is not None:
                    payload["score"] = float(payload["score"])
                results.append(payload)
        else:
            projects: Dict[tuple, Dict[str, Any]] = {}
            for row in rows:
                row_dict = dict(row)
                score = float(row_dict.get("score") or 0.0)
                key = (
                    row_dict.get("title") or "",
                    row_dict.get("type") or "",
                    row_dict.get("number") or 0,
                    row_dict.get("year") or 0,
                    row_dict.get("house") or "",
                )
                if key not in projects:
                    projects[key] = {
                        "id": row_dict.get("id"),
                        "title": row_dict.get("title"),
                        "house": row_dict.get("house"),
                        "type": row_dict.get("type"),
                        "number": row_dict.get("number"),
                        "presentation_date": row_dict.get("presentation_date"),
                        "year": row_dict.get("year"),
                        "author": row_dict.get("author"),
                        "subject": row_dict.get("subject"),
                        # HACKISH: Renaming full_text to chunk_text in output for API compatibility
                        # TODO: Standardize field naming across database schema and API responses
                        "chunk_text": row_dict.get("full_text"),
                        "url": row_dict.get("url"),
                        "scraped_at": row_dict.get("scraped_at"),
                        "metadata": row_dict.get("metadata"),
                        "chunks": [],
                        "score": 0.0,
                        "chunk_count": 0,
                    }
                project = projects[key]
                chunk = {
                    "id": row_dict.get("id"),
                    "chunk_number": row_dict.get("chunk_number"),
                    "score": score,
                }
                if detail:
                    chunk["chunk_text"] = row_dict.get("chunk_text")
                project["chunks"].append(chunk)
                project["score"] += score
                project["chunk_count"] += 1

            # Sort chunks within each project by score descending
            for project in projects.values():
                project["chunks"].sort(key=lambda c: c["score"], reverse=True)
                # Normalize score to average
                if project["chunk_count"] > 0:
                    project["score"] /= project["chunk_count"]

            # Sort projects by score descending
            results = sorted(projects.values(), key=lambda p: p["score"], reverse=True)
        elapsed_ms = (perf_counter() - start) * 1000.0
        return (results, elapsed_ms) if return_latency else results

    def check_documents_exist(
        self, documents: List[Dict[str, Any]], sample_size: int = 5
    ) -> Dict[str, Any]:
        """
        Check if documents from the sample already exist in the vector store.
        
        Args:
            documents: List of document dicts with title, type, number, year, house fields
            sample_size: Number of documents from the beginning to check (default: 5)
        
        Returns:
            Dict with:
                - total_checked: number of documents checked
                - existing_count: number of documents found in DB
                - existing_documents: list of matched documents with details
                - all_exist: boolean indicating if all checked documents exist
        """
        sample = documents[:sample_size]
        existing_documents = []
        
        for doc in sample:
            # Build query to find exact match
            title = doc.get("title")
            doc_type = doc.get("type")
            number = doc.get("number")
            year = doc.get("year")
            house = doc.get("house")
            
            # Skip documents without sufficient identifying information
            if not title:
                continue
            
            # Query for exact match
            query = text("""
                SELECT DISTINCT title, type, number, year, house, COUNT(*) as chunk_count
                FROM projetos_referencias
                WHERE title = :title
                AND (:type IS NULL OR type = :type)
                AND (:number IS NULL OR number = :number)
                AND (:year IS NULL OR year = :year)
                AND (:house IS NULL OR house = :house)
                GROUP BY title, type, number, year, house
                LIMIT 1
            """)
            
            result = self.session.execute(
                query,
                {
                    "title": title,
                    "type": doc_type,
                    "number": number,
                    "year": year,
                    "house": house,
                }
            ).mappings().first()
            
            if result:
                existing_documents.append({
                    "title": result["title"],
                    "type": result["type"],
                    "number": result["number"],
                    "year": result["year"],
                    "house": result["house"],
                    "chunk_count": result["chunk_count"],
                })
        
        return {
            "total_checked": len(sample),
            "existing_count": len(existing_documents),
            "existing_documents": existing_documents,
            "all_exist": len(existing_documents) == len(sample) and len(sample) > 0,
        }

    def stats(self, use_cache: bool = True) -> Dict[str, int]:
        """
        Get vector store statistics (chunks and projects count).
        
        Args:
            use_cache: If True, uses cached results (TTL configurable via
                      VECTOR_STATS_CACHE_TTL env var, default 5 minutes).
                      Set to False to force a fresh database query.
        """
        global _stats_cache
        
        # Check cache validity
        now = time()
        if use_cache and _stats_cache["data"] is not None:
            age = now - _stats_cache["timestamp"]
            if age < _get_stats_cache_ttl():
                return _stats_cache["data"]
        
        # Query database
        result = self.session.execute(
            text(
                """
                SELECT
                    COUNT(*)::INT AS chunks,
                    COUNT(DISTINCT title)::INT AS projects
                FROM projetos_referencias
                """
            )
        ).mappings().first()
        
        if not result:
            data = {"chunks": 0, "projects": 0}
        else:
            data = {
                "chunks": int(result.get("chunks", 0) or 0),
                "projects": int(result.get("projects", 0) or 0),
            }
        
        # Update cache
        _stats_cache["data"] = data
        _stats_cache["timestamp"] = now
        
        return data

    def get_summary_by_house_and_year(self) -> Dict[str, Any]:
        """
        Get summary statistics grouped by house and year.
        
        Returns:
            Dict with:
                - houses: list of {house, years: [{year, count}]}
                - total_projects: total unique projects count
        """
        # Query for house and year breakdown
        result = self.session.execute(
            text("""
                SELECT 
                    COALESCE(house, 'Sem casa') as house,
                    COALESCE(year, 0) as year,
                    COUNT(DISTINCT title) as project_count
                FROM projetos_referencias
                GROUP BY house, year
                ORDER BY house, year DESC
            """)
        ).mappings().all()
        
        # Group by house
        houses_dict = {}
        for row in result:
            house = row["house"]
            year = row["year"]
            count = row["project_count"]
            
            if house not in houses_dict:
                houses_dict[house] = {"house": house, "years": []}
            
            houses_dict[house]["years"].append({"year": year, "count": count})
        
        # Convert to list
        houses_list = list(houses_dict.values())
        
        # Get total projects
        total = self.session.execute(
            text("SELECT COUNT(DISTINCT title) as total FROM projetos_referencias")
        ).mappings().first()
        
        return {
            "houses": houses_list,
            "total_projects": total["total"] if total else 0
        }

    def reindex(
        self,
        provider: "EmbeddingProvider",
        *,
        batch_size: int = 64,
    ) -> Dict[str, int]:
        if batch_size <= 0:
            raise ValueError("batch_size deve ser maior que zero.")

        rows = self.session.execute(
            text("SELECT id, chunk_text FROM projetos_referencias ORDER BY id")
        ).mappings().all()
        total = len(rows)
        if total == 0:
            return {"updated": 0, "skipped": 0, "total": 0}

        update_stmt = text(
            "UPDATE projetos_referencias SET embedding = :embedding WHERE id = :id"
        ).bindparams(
            bindparam(
                "embedding",
                type_=ProjetoReferencia.__table__.c.embedding.type,
            ),
            bindparam("id"),
        )

        updated = 0
        skipped = 0
        for start_idx in range(0, total, batch_size):
            batch = rows[start_idx : start_idx + batch_size]
            valid_pairs = [
                (row["id"], (row["chunk_text"] or "").strip())
                for row in batch
                if (row["chunk_text"] or "").strip()
            ]
            skipped += len(batch) - len(valid_pairs)
            if not valid_pairs:
                continue

            texts = [text_value for _, text_value in valid_pairs]
            vectors = provider.embed(texts)
            if len(vectors) != len(valid_pairs):
                raise RuntimeError(
                    "Quantidade de embeddings divergente dos chunks reindexados."
                )

            params = [
                {"id": row_id, "embedding": vector}
                for (row_id, _), vector in zip(valid_pairs, vectors)
            ]
            self.session.execute(update_stmt, params)
            updated += len(params)

        self.session.commit()
        return {"updated": updated, "skipped": skipped, "total": total}

    def top_projects(
        self,
        embedding: List[float],
        *,
        limit: int,
        offset: int = 0,
        fetch_multiplier: int = 3,
    ) -> Dict[str, Any]:
        base_limit = max(50, (limit + offset) * fetch_multiplier)
        results = self.search(embedding, limit=base_limit, offset=0)

        projects: Dict[str, Dict[str, Any]] = {}
        for item in results:
            title = item.get("title") or "—"
            project = projects.setdefault(
                title,
                {
                    "title": title,
                    "house": item.get("house"),
                    "author": item.get("author"),
                    "subject": item.get("subject"),
                    # HACKISH: Renaming full_text to chunk_text in output for API compatibility
                    # TODO: Standardize field naming across database schema and API responses
                    "chunk_text": item.get("full_text"),
                    "year": item.get("year"),
                    "metadata": item.get("metadata"),
                    "chunks": [],
                    "score": 0.0,
                },
            )
            project["chunks"].append(
                {
                    "chunk_text": item.get("chunk_text"),
                    "chunk_number": item.get("chunk_number"),
                    "score": item.get("score"),
                }
            )
            score_value = float(item.get("score") or 0.0)
            project["score"] += score_value

        sorted_projects = sorted(
            projects.values(),
            key=lambda entry: (len(entry["chunks"]), entry["score"]),
            reverse=True,
        )

        paginated = sorted_projects[offset : offset + limit]
        # Normalize score by number of chunks
        for proj in paginated:
            chunk_count = max(len(proj["chunks"]), 1)
            proj["score"] = proj["score"] / chunk_count

        return {
            "projects": paginated,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "total_projects": len(sorted_projects),
                "total_returned": len(paginated),
                "has_more": offset + limit < len(sorted_projects),
            },
        }


__all__ = ["VectorDocument", "VectorStorePgVector", "invalidate_stats_cache"]
