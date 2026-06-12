"""Regression test for transient-error retry in bluesky_handler — no network.

Found in the 2026-06-12 code review: retryability was decided by substring
match on str(e), but atproto's RequestException never sets exception args, so
str(e) is always '' — transient 429/5xx errors were NEVER retried. Detection
must use the response status code instead, and must not false-positive on
'429'-like text in an error body.

Run from the repo root:
    .venv/bin/python scripts/test_bluesky_retry.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from atproto_client.exceptions import InvokeTimeoutError, RequestException
from atproto_client.request import Response
from src import bluesky_handler


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


SENT_POST = object()


def make_request_exception(status_code: int, content=None) -> RequestException:
    return RequestException(
        Response(success=False, status_code=status_code, content=content, headers={})
    )


def run_case(name: str, login_errors: list, expect_result: bool, expect_attempts: int) -> None:
    """Drive post_content_to_bluesky with a fake Client whose login raises the
    given errors in order (None = success), then assert outcome and attempt count.
    """
    attempts = {"count": 0}

    class FakeClient:
        def __init__(self):
            attempts["count"] += 1
            self._error = (
                login_errors[attempts["count"] - 1]
                if attempts["count"] <= len(login_errors)
                else None
            )

        def login(self, identifier, password):
            if self._error is not None:
                raise self._error

        def send_post(self, text, facets=None, embed=None):
            return SENT_POST

    orig_client = bluesky_handler.Client
    orig_sleep = bluesky_handler.time.sleep
    try:
        bluesky_handler.Client = FakeClient
        bluesky_handler.time.sleep = lambda s: None
        result = bluesky_handler.post_content_to_bluesky(
            "user.test", "password", "hello", [], None
        )
    finally:
        bluesky_handler.Client = orig_client
        bluesky_handler.time.sleep = orig_sleep

    got_result = result is SENT_POST
    if got_result != expect_result:
        fail(f"{name}: expected result={expect_result}, got {result!r}")
    if attempts["count"] != expect_attempts:
        fail(f"{name}: expected {expect_attempts} attempts, got {attempts['count']}")
    print(f"[OK ] {name}")


# Transient 503 on first attempt must be retried and then succeed
run_case(
    "503 is retried",
    [make_request_exception(503)],
    expect_result=True,
    expect_attempts=2,
)

# Rate limiting (429) is transient too
run_case(
    "429 is retried",
    [make_request_exception(429)],
    expect_result=True,
    expect_attempts=2,
)

# A 400 must not be retried, even if the error body happens to contain '429'
run_case(
    "400 with '429' in body is not retried",
    [make_request_exception(400, content="record size 4290 exceeds limit")] * 3,
    expect_result=False,
    expect_attempts=1,
)

# Timeouts keep their existing retry behavior
run_case(
    "timeout is retried",
    [InvokeTimeoutError()],
    expect_result=True,
    expect_attempts=2,
)

print("All bluesky-retry checks passed.")
