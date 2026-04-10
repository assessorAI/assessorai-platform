from __future__ import annotations

from typing import Iterable, List, Sequence

from ..base import EmbeddingProvider

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore

try:
    from openai import OpenAI
    from openai import OpenAIError
except ImportError:  # pragma: no cover - handled at runtime when provider is requested
    OpenAI = None  # type: ignore
    OpenAIError = Exception  # type: ignore


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Embedding provider backed by OpenAI's embeddings API."""

    def __init__(
        self,
        *,
        model_name: str,
        api_key: str,
        api_base: str | None = None,
        timeout: float | None = None,
    ):
        if OpenAI is None:  # pragma: no cover - import guard
            raise RuntimeError(
                "The 'openai' package is not installed. "
                "Add it to requirements to use the OpenAI embedding provider."
            )

        client_kwargs = {"api_key": api_key}
        if api_base:
            client_kwargs["base_url"] = api_base

        # Avoid OpenAI creating its own httpx.Client with incompatible kwargs
        # (e.g. httpx>=0.28 removed the 'proxies' parameter).
        if httpx is not None:
            http_client_kwargs = {}
            if timeout is not None:
                http_client_kwargs["timeout"] = timeout
            client_kwargs["http_client"] = httpx.Client(**http_client_kwargs)
        elif timeout is not None:
            client_kwargs["timeout"] = timeout

        self._client = OpenAI(**client_kwargs)
        self.model_name = model_name
        self.name = f"openai:{model_name}"

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        inputs: Sequence[str] = [
            text.strip() for text in texts if text and text.strip()
        ]
        if not inputs:
            return []
        try:
            response = self._client.embeddings.create(
                model=self.model_name,
                input=list(inputs),
            )
        except OpenAIError as exc:  # pragma: no cover - network error path
            raise RuntimeError(f"OpenAI embedding request failed: {exc}") from exc

        return [
            list(item.embedding)  # type: ignore[return-value]
            for item in response.data
        ]


__all__ = ["OpenAIEmbeddingProvider"]
