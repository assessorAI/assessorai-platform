from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

import tiktoken
from sqlalchemy.orm import Session

from .embeddings import EmbeddingProvider, get_embedding_dimension
from .vector_store import VectorDocument, VectorStorePgVector


@dataclass
class ImportItem:
    title: Optional[str]
    house: Optional[str]
    type: Optional[str]
    number: Optional[int]
    presentation_date: Optional[str]
    year: Optional[int]
    author: Optional[List[str]]
    subject: Optional[str]
    full_text: Optional[str]
    length: Optional[int]
    url: Optional[str]
    scraped_at: Optional[str]
    metadata: Optional[Dict[str, Any]]


def _tokeniser(model: str) -> tiktoken.Encoding:
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def chunk_text(
    text: str,
    *,
    max_tokens: int,
    overlap_tokens: int,
    model: str,
) -> List[Dict[str, Any]]:
    if not text:
        return []

    encoding = _tokeniser(model)
    tokens = encoding.encode(text)
    if not tokens:
        return []

    chunks: List[Dict[str, Any]] = []
    cursor = 0
    while cursor < len(tokens):
        end = min(cursor + max_tokens, len(tokens))
        chunk_tokens = tokens[cursor:end]
        chunk_text_value = encoding.decode(chunk_tokens)

        if end < len(tokens):
            last_space = chunk_text_value.rfind(" ")
            if last_space > 0:
                chunk_text_value = chunk_text_value[: last_space + 1]
                end = cursor + len(encoding.encode(chunk_text_value))

        chunks.append({"text": chunk_text_value, "number": len(chunks)})

        if end >= len(tokens):
            break

        cursor = max(end - overlap_tokens, 0)
        if cursor <= len(tokens):
            overlap_slice = tokens[cursor:end]
            if overlap_slice:
                overlap_decoded = encoding.decode(overlap_slice)
                first_space = overlap_decoded.find(" ")
                if first_space > 0:
                    adjust = len(encoding.encode(overlap_decoded[: first_space + 1]))
                    cursor = end - adjust

    return chunks


def prepare_documents(
    items: Iterable[ImportItem],
    *,
    chunk_full_text: bool,
    chunk_size: int,
    overlap_tokens: int,
    chunk_model: str,
) -> List[VectorDocument]:
    documents: List[VectorDocument] = []
    for item in items:
        author_list = item.author or []
        if isinstance(author_list, str):
            author_values = [author_list]
        else:
            author_values = list(author_list)

        metadata_value = item.metadata
        if isinstance(metadata_value, str):
            try:
                metadata_value = json.loads(metadata_value)
            except json.JSONDecodeError:
                metadata_value = {"raw": metadata_value}

        base_payload = {
            "title": item.title,
            "house": item.house,
            "type": item.type,
            "number": item.number,
            "presentation_date": item.presentation_date,
            "year": item.year,
            "author": author_values or None,
            "subject": item.subject,
            "length": item.length,
            "url": item.url,
            "scraped_at": item.scraped_at,
            "metadata": metadata_value,
        }

        text_source = item.full_text or item.subject or ""
        if not text_source:
            continue

        chunks: List[Dict[str, Any]]
        if chunk_full_text:
            chunks = chunk_text(
                text_source,
                max_tokens=chunk_size,
                overlap_tokens=overlap_tokens,
                model=chunk_model,
            )
        else:
            chunks = []
        if not chunks:
            chunks = [{"text": text_source, "number": 0}]

        for chunk in chunks:
            # Keep full_text only on chunk 0 to avoid duplicating large strings
            # across all rows/chunks.
            full_text_value = item.full_text if chunk.get("number") == 0 else None
            documents.append(
                VectorDocument(
                    chunk_text=chunk["text"],
                    chunk_number=chunk["number"],
                    full_text=full_text_value,
                    embedding=[],  # placeholder, filled later
                    **base_payload,
                )
            )
    return documents


def assign_embeddings(
    documents: List[VectorDocument],
    *,
    provider: EmbeddingProvider,
) -> None:
    if not documents:
        return

    try:
        batch_size = max(1, int(os.getenv("EMBEDDING_BATCH_SIZE", "100")))
    except ValueError:
        batch_size = 100

    expected_dim: Optional[int] = None
    for start in range(0, len(documents), batch_size):
        batch_docs = documents[start : start + batch_size]
        texts = [doc.chunk_text for doc in batch_docs]
        vectors = provider.embed(texts)
        if len(vectors) != len(batch_docs):
            raise RuntimeError("Quantidade de embeddings divergente dos documentos do lote atual.")
        if not vectors:
            continue
        if expected_dim is None:
            expected_dim = get_embedding_dimension(len(vectors[0]))
        for doc, vector in zip(batch_docs, vectors):
            if expected_dim and len(vector) != expected_dim:
                raise ValueError(
                    f"Dimensão do embedding ({len(vector)}) diferente da configurada ({expected_dim})."
                )
            doc.embedding = vector

    for doc in documents:
        if not doc.embedding:
            raise RuntimeError("O provedor não retornou embedding para um dos documentos.")


def ingest_documents(
    session: Session,
    *,
    provider: EmbeddingProvider,
    items: Iterable[ImportItem],
    chunk_full_text: bool,
    chunk_size: int,
    overlap_tokens: int,
    chunk_model: str,
    truncate_before_insert: bool,
) -> Dict[str, Any]:
    """
    Ingest documents with streaming/batch processing to prevent OOM on large imports.
    
    Process items in batches to avoid loading everything into memory at once.
    This is critical for imports with 500+ documents.
    """
    store = VectorStorePgVector(session)
    
    # Get batch size from environment (default: 50 items at a time)
    try:
        items_batch_size = max(1, int(os.getenv("VECTOR_IMPORT_BATCH_SIZE", "50")))
    except ValueError:
        items_batch_size = 50
    
    # Convert to list only to count and batch
    items_list = list(items)
    total_items = len(items_list)
    
    if not items_list:
        return {"items": 0, "chunks": 0}
    
    # Truncate once at the beginning if requested
    if truncate_before_insert:
        store.truncate()
    
    total_chunks_inserted = 0
    
    # Process in batches to limit memory usage
    for batch_start in range(0, total_items, items_batch_size):
        batch_end = min(batch_start + items_batch_size, total_items)
        batch_items = items_list[batch_start:batch_end]
        
        # Prepare documents for this batch
        documents = prepare_documents(
            batch_items,
            chunk_full_text=chunk_full_text,
            chunk_size=chunk_size,
            overlap_tokens=overlap_tokens,
            chunk_model=chunk_model,
        )
        
        if not documents:
            continue
        
        # Assign embeddings for this batch
        assign_embeddings(documents, provider=provider)
        
        # Insert this batch
        inserted = store.bulk_insert(documents)
        total_chunks_inserted += inserted
        
        # Log progress for large imports
        if total_items > items_batch_size:
            progress_pct = ((batch_end) / total_items) * 100
            print(f"[vector_ingestion] Processed {batch_end}/{total_items} items ({progress_pct:.1f}%) - {inserted} chunks inserted")
    
    return {"items": total_items, "chunks": total_chunks_inserted}


__all__ = [
    "ImportItem",
    "chunk_text",
    "ingest_documents",
]
