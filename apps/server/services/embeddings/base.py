from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List


class EmbeddingProvider(ABC):
    """Interface for embedding providers."""

    name: str

    @abstractmethod
    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        """Return embeddings for the given texts."""
        raise NotImplementedError


class UnsupportedProviderError(RuntimeError):
    """Raised when the requested embedding provider is not supported."""

    pass


__all__ = ["EmbeddingProvider", "UnsupportedProviderError"]
