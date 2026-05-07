"""Suppress noisy pydantic deprecation warnings emitted by atproto.

Importing this module registers a `warnings` filter that hides
`PydanticDeprecatedSince20`. Suppression lives in Python code (rather
than `PYTHONWARNINGS`) because the env var is parsed during interpreter
startup, before user packages are reliably importable for category
resolution — Python prints "Invalid -W option ignored" instead of
applying the filter.

Import this module from the application entry point before any code
that may trigger the warning (notably `atproto`).
"""
from __future__ import annotations

import warnings


def apply() -> None:
    """Register the suppression filter. Idempotent."""
    try:
        from pydantic import PydanticDeprecatedSince20
    except ImportError:
        # pydantic not installed — nothing to suppress. Caller will likely
        # fail elsewhere; we don't want this helper to be the cause.
        return
    warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)


# Apply on import so a single `import src.utils.warnings_setup` is enough.
apply()
