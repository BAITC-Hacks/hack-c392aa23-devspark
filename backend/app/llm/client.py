"""OpenAI-compatible client, configured from the environment and cleanly disabled
without a key so the whole app still runs in rules mode."""

from __future__ import annotations

import os
from functools import lru_cache


def model_name() -> str:
    return os.environ.get("LLM_MODEL") or "gpt-4.1-mini"


def timeout_s() -> float:
    try:
        return float(os.environ.get("LLM_TIMEOUT_S", "8"))
    except ValueError:
        return 8.0


@lru_cache(maxsize=1)
def get_client():
    """Return an OpenAI client, or None when no key is configured."""

    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        return None
    base_url = os.environ.get("LLM_BASE_URL") or None
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_s())


def llm_enabled() -> bool:
    return get_client() is not None
