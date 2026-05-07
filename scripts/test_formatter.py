"""Local sanity check for post_formatter — no network calls.

Verifies the formatter never produces a post that exceeds Bluesky's 300-grapheme
limit, including the long-URL case from the 2026-05-06 production failure.

Run from the repo root:
    .venv/bin/python scripts/test_formatter.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.post_formatter import (
    BLUESKY_CHAR_LIMIT,
    count_graphemes,
    format_bluesky_post_from_raindrop,
    strip_tracking_params,
)


def case(name: str, raindrop: dict, expect_fits: bool = True) -> None:
    """Run the formatter on a raindrop dict and assert the output fits the limit.

    If `expect_fits` is False, we tolerate going over (used for the unpostable
    edge case where the URL alone exceeds the limit).
    """
    # Skip cover so we don't hit the network for image embeds
    raindrop = {**raindrop, "cover": ""}
    text, facets, _ = format_bluesky_post_from_raindrop(raindrop)
    g = count_graphemes(text)
    fits = g <= BLUESKY_CHAR_LIMIT
    if expect_fits:
        status = "OK " if fits else "FAIL"
    else:
        status = "OK " if not fits else "OK "  # either outcome is acceptable
    print(f"[{status}] {name}: {g} graphemes")
    print(f"        text: {text!r}")
    if expect_fits and not fits:
        raise SystemExit(1)


# --- strip_tracking_params unit checks ---
expected = "https://www.bloomberg.com/news/articles/2026-05-06/microsoft-clean-power-target-on-chopping-block-over-data-center-boom"
got = strip_tracking_params(
    "https://www.bloomberg.com/news/articles/2026-05-06/microsoft-clean-power-target-on-chopping-block-over-data-center-boom"
    "?cmpid=BBD050626_GREENDAILY&utm_campaign=greendaily&utm_medium=email"
    "&utm_source=newsletter&utm_term=260506&utm_content=4212"
)
assert got == expected, f"strip_tracking_params: got {got!r}"
print(f"[OK ] strip_tracking_params strips utm_* and cmpid")

# Preserves load-bearing params
got = strip_tracking_params("https://example.com/search?q=python&utm_source=newsletter")
assert got == "https://example.com/search?q=python", got
print(f"[OK ] strip_tracking_params preserves q=")

# Handles no query string
assert strip_tracking_params("https://example.com/path") == "https://example.com/path"
print(f"[OK ] strip_tracking_params handles no query")


# --- formatter cases ---

# Reproduces the 2026-05-06 production failure (got 318, max 300)
case(
    "bloomberg-tracking-bloat (the failing case)",
    {
        "_id": 1708285949,
        "title": "Microsoft in Talks to Ax Key Energy Pledge Amid Data Center Boom",
        "link": (
            "https://www.bloomberg.com/news/articles/2026-05-06/"
            "microsoft-clean-power-target-on-chopping-block-over-data-center-boom"
            "?cmpid=BBD050626_GREENDAILY&utm_campaign=greendaily&utm_medium=email"
            "&utm_source=newsletter&utm_term=260506&utm_content=4212"
        ),
        "note": "",
        "excerpt": "Microsoft Corp. is in discussions...",
    },
)

# Long URL with no tracking — exercises the safety-net retry path
case(
    "long-url-no-tracking",
    {
        "_id": 1,
        "title": "A reasonably long article title that takes up some of the budget",
        "link": "https://example.com/" + "a" * 220,
        "note": "",
        "excerpt": "",
    },
)

# Skeet content present
case(
    "with-skeet-content",
    {
        "_id": 2,
        "title": "Article Title",
        "link": "https://example.com/article",
        "note": "[skeet_content: Worth a read — flags a real issue.]",
        "excerpt": "",
    },
)

# URL longer than the 300-grapheme budget — known unpostable edge case.
# We document it but don't fail the suite; Bluesky will reject it.
case(
    "url-exceeds-budget (known unpostable)",
    {
        "_id": 3,
        "title": "Some Title",
        "link": "https://example.com/" + "x" * 320,
        "note": "",
        "excerpt": "",
    },
    expect_fits=False,
)

# Short normal post — no truncation expected
case(
    "short-post",
    {
        "_id": 4,
        "title": "Short Title",
        "link": "https://example.com/foo",
        "note": "",
        "excerpt": "",
    },
)

# URL with non-tracking ampersand params + tight budget — exercises the
# build/measure/retry path if atproto percent-encodes `&` on build_text().
case(
    "ampersands-tight-budget",
    {
        "_id": 5,
        "title": (
            "A long title designed to consume most of the post budget so any URL "
            "expansion from percent-encoding pushes us over the limit and forces a rebuild "
            "to verify the safety-net path actually shrinks the body and re-measures correctly"
        ),
        "link": (
            "https://example.com/search"
            "?q=cats&page=2&sort=desc&filter=recent&category=animals&country=us&format=json"
        ),
        "note": "",
        "excerpt": "",
    },
)

print("\nAll cases passed.")
