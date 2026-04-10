from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List, Tuple

from .base import EmbeddingProvider, UnsupportedProviderError
from .providers.openai import OpenAIEmbeddingProvider
from .providers import openai as openai_provider_module


DEFAULT_OPENAI_MODEL = "text-embedding-3-small"

_PROVIDER_REGISTRY = {
    "openai": OpenAIEmbeddingProvider,
}

_OPENAI_MODEL_DIMENSIONS: Dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}

_VISIBLE_PROVIDERS = ["openai"]
_PROVIDER_LABELS = {
    "openai": "OpenAI Embeddings",
}


def _resolve_provider_name(explicit: str | None = None) -> str:
    provider = explicit or os.getenv("EMBEDDING_PROVIDER", "openai")
    return provider.lower()


def _resolve_model_name(provider: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    return (
        os.getenv("OPENAI_EMBEDDING_MODEL")
        or os.getenv("EMBEDDING_MODEL")
        or DEFAULT_OPENAI_MODEL
    )


def _collect_openai_credentials() -> Tuple[str, str | None, float | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required to use the OpenAI embedding provider.")
    api_base = os.getenv("OPENAI_API_BASE")
    timeout_value = os.getenv("OPENAI_TIMEOUT")
    timeout = None
    if timeout_value:
        try:
            timeout = float(timeout_value)
        except ValueError:
            timeout = None
    return api_key, api_base, timeout


@lru_cache(maxsize=8)
def get_embedding_provider(
    provider: str | None = None,
    model_name: str | None = None,
) -> EmbeddingProvider:
    resolved_provider = _resolve_provider_name(provider)
    resolved_model = _resolve_model_name(resolved_provider, model_name)

    provider_cls = _PROVIDER_REGISTRY.get(resolved_provider)
    if not provider_cls:
        raise UnsupportedProviderError(f"Embedding provider '{resolved_provider}' não suportado.")

    if resolved_provider != "openai":
        raise UnsupportedProviderError(f"Embedding provider '{resolved_provider}' não suportado.")

    api_key, api_base, timeout = _collect_openai_credentials()
    return provider_cls(
        model_name=resolved_model,
        api_key=api_key,
        api_base=api_base,
        timeout=timeout,
    )


def get_embedding_dimension(default: int = 384) -> int:
    env_value = os.getenv("EMBEDDING_DIM")
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            pass

    provider = _resolve_provider_name()
    model = _resolve_model_name(provider)

    if provider == "openai":
        return _OPENAI_MODEL_DIMENSIONS.get(model, default)

    return default


def resolve_current_provider() -> str:
    return _resolve_provider_name()


def resolve_current_model(provider: str | None = None) -> str:
    resolved_provider = provider or _resolve_provider_name()
    return _resolve_model_name(resolved_provider)


def list_available_providers() -> List[Dict[str, str | bool]]:
    items: List[Dict[str, str | bool]] = []
    seen = set()
    openai_available = openai_provider_module.OpenAI is not None and bool(os.getenv("OPENAI_API_KEY"))
    for provider_id in _VISIBLE_PROVIDERS:
        if provider_id in seen or provider_id not in _PROVIDER_REGISTRY:
            continue
        seen.add(provider_id)
        if provider_id == "openai" and not openai_available:
            continue
        items.append(
            {
                "id": provider_id,
                "label": _PROVIDER_LABELS.get(provider_id, provider_id.title()),
                "available": True,
                "default_model": _resolve_model_name(provider_id),
            }
        )
    return items


__all__ = [
    "get_embedding_provider",
    "get_embedding_dimension",
    "resolve_current_provider",
    "resolve_current_model",
    "list_available_providers",
]
