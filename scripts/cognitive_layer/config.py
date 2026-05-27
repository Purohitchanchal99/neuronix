"""Configuration for Cognitive Layer v1."""

import os


def llm_enabled() -> bool:
    """Return whether external LLM providers are allowed.

    Cognitive Layer v1 should default to OFF.
    """
    return os.getenv("NEURONIX_LLM_ENABLED", "false").strip().lower() in {"1", "true", "yes", "y"}

