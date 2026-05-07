"""Verify that importing src.utils.warnings_setup registers a warnings
filter that ignores pydantic's PydanticDeprecatedSince20.

The previous approach used PYTHONWARNINGS in entrypoint.sh, but Python
parses that env var early in interpreter startup, before pydantic is
reliably importable for category resolution — so it logged
"Invalid -W option ignored" on every container start. This module-based
suppression runs at user-code time, where pydantic is fully importable.

Run from the repo root:
    .venv/bin/python scripts/test_warnings_setup.py
"""
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Reset filters so we know exactly what's registered after the import.
warnings.resetwarnings()

from src.utils import warnings_setup  # noqa: F401  - import for side effect
from pydantic import PydanticDeprecatedSince20

# 1. Assert the filter is registered with action="ignore" for our category.
matching = [
    f for f in warnings.filters
    if f[0] == "ignore" and f[2] is PydanticDeprecatedSince20
]
assert matching, (
    f"Expected an ignore filter for PydanticDeprecatedSince20; "
    f"current filters: {warnings.filters}"
)
print("[OK ] filter registered for PydanticDeprecatedSince20")

# 2. Assert that a warning of that category is actually suppressed.
with warnings.catch_warnings(record=True) as caught:
    # catch_warnings() resets filters; reapply our filter inside.
    warnings_setup.apply()
    warnings.warn("dummy deprecation", category=PydanticDeprecatedSince20)
    suppressed = [w for w in caught if issubclass(w.category, PydanticDeprecatedSince20)]
    assert not suppressed, (
        f"Warning leaked through filter: {[str(w.message) for w in suppressed]}"
    )
print("[OK ] PydanticDeprecatedSince20 warnings are suppressed")

print("\nAll warnings-setup tests passed.")
