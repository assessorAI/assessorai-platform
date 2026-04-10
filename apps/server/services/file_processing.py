from __future__ import annotations

import io
import logging
from typing import Optional, List
import os

logger = logging.getLogger(__name__)

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False
    logger.warning("pypdf not installed, PDF text extraction will not be available")

try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    logger.warning("python-docx not installed, DOCX text extraction will not be available")


class FileTextExtractor:
    """Service for extracting text from various file formats."""

    @staticmethod
    def extract_text(file_content: bytes, content_type: str) -> Optional[str]:
        """Extract text from file based on content type."""
        try:
            if content_type == "application/pdf" and HAS_PYPDF:
                return FileTextExtractor._extract_pdf_text(file_content)
            elif content_type in [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"
            ] and HAS_DOCX:
                return FileTextExtractor._extract_docx_text(file_content)
            elif content_type.startswith("text/"):
                return FileTextExtractor._extract_text_content(file_content)
            else:
                logger.info(f"No text extraction available for content type: {content_type}")
                return None
        except Exception as e:
            logger.warning(f"Failed to extract text: {e}")
            return None

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        """Extract text from PDF file."""
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text.strip():
                text_parts.append(page_text)

        return "\n".join(text_parts).strip()

    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        """Extract text from DOCX file."""
        docx_file = io.BytesIO(content)
        document = Document(docx_file)
        text_parts = []

        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        # Also extract from tables
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text)

        return "\n".join(text_parts).strip()

    @staticmethod
    def _extract_text_content(content: bytes) -> str:
        """Extract text from plain text files."""
        try:
            return content.decode("utf-8", errors="ignore").strip()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            return content.decode("latin-1", errors="ignore").strip()


def should_generate_embeddings(file_size: int, content_type: str) -> bool:
    """Determine if file should have embeddings generated."""
    from .embeddings import get_embedding_provider

    # Check if embeddings are configured
    try:
        provider = get_embedding_provider()
        if not provider:
            return False
    except Exception:
        return False

    # Only generate for text-extractable files
    text_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
        "text/plain",
        "text/markdown",
        "text/html"
    ]

    # Size limit (configurable)
    max_size = int(os.getenv("MAX_EMBEDDING_FILE_SIZE", "10_000_000"))  # 10MB default

    return content_type in text_types and file_size <= max_size


def generate_file_embedding(text: str, provider) -> Optional[List[float]]:
    """Generate embedding for file text."""
    if not text or not provider:
        return None

    try:
        # Clean and prepare text
        text = text.strip()
        if not text:
            return None

        # For now, generate single embedding for the entire text
        # In the future, this could be enhanced with chunking for large files
        embeddings = provider.embed([text])
        return embeddings[0] if embeddings else None
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
        return None