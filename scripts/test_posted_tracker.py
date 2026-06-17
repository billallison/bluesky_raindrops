"""Regression tests for posted_tracker and the already-posted skip path.

Covers two bugs found in the 2026-06-12 code review:
1. Skipping an already-posted raindrop never re-attempted tag removal, so a
   permanently failed removal left the item stuck — and after RETENTION_DAYS
   the tracker entry expired and the item double-posted. Now the skip path
   retries removal (self-healing) and retention is 90 days.
2. _save_tracker wrote the JSON in place; a crash mid-write truncated the
   file and erased the posted history. Now writes are atomic (temp + replace).

Run from the repo root:
    .venv/bin/python scripts/test_posted_tracker.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils import posted_tracker
from src import raindrop_handler


def fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    raise SystemExit(1)


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.text = json.dumps(payload)

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


# --- 1a. Skip path re-attempts tag removal (self-healing) ---

removal_attempts = []

def run_skip_path_check():
    items = [
        {"_id": 111, "title": "already posted, tag stuck"},
        {"_id": 222, "title": "fresh item"},
    ]

    orig_get = raindrop_handler.requests.get
    orig_already = raindrop_handler.is_already_posted
    orig_remove = raindrop_handler.remove_toskeet_tag
    try:
        raindrop_handler.requests.get = lambda *a, **k: FakeResponse({"items": items})
        raindrop_handler.is_already_posted = lambda rid: rid == 111
        raindrop_handler.remove_toskeet_tag = (
            lambda token, rid, tag="toskeet": removal_attempts.append(rid) or True
        )

        result = raindrop_handler.get_latest_raindrop_to_skeet("fake-token")
    finally:
        raindrop_handler.requests.get = orig_get
        raindrop_handler.is_already_posted = orig_already
        raindrop_handler.remove_toskeet_tag = orig_remove

    if result is None or result["_id"] != 222:
        fail(f"expected fresh item 222 to be returned, got {result!r}")
    if 111 not in removal_attempts:
        fail("skip path did not re-attempt tag removal for already-posted item 111")
    if 222 in removal_attempts:
        fail("tag removal must not run for the item being returned (main flow handles it)")
    print("[OK ] skip path re-attempts tag removal for already-posted items")


run_skip_path_check()


# --- 1b. Retention is long enough to outlive a stuck tag ---

if posted_tracker.RETENTION_DAYS < 90:
    fail(f"RETENTION_DAYS is {posted_tracker.RETENTION_DAYS}, expected >= 90")
print(f"[OK ] retention is {posted_tracker.RETENTION_DAYS} days")


# --- 2. A failed save must not destroy the existing tracker file ---

with tempfile.TemporaryDirectory() as tmpdir:
    orig_tracker_file = posted_tracker.TRACKER_FILE
    posted_tracker.TRACKER_FILE = os.path.join(tmpdir, "posted_raindrops.json")
    try:
        posted_tracker.mark_as_posted(12345, "at://did:plc:x/app.bsky.feed.post/y")
        before = posted_tracker._load_tracker()
        if "12345" not in before.get("posted", {}):
            fail("setup: initial mark_as_posted did not persist")

        # Simulate a crash mid-serialization on the next save
        orig_dump = posted_tracker.json.dump

        def exploding_dump(*args, **kwargs):
            raise IOError("disk full mid-write")

        posted_tracker.json.dump = exploding_dump
        try:
            posted_tracker.mark_as_posted(67890)
        except Exception:
            pass  # save failure may be swallowed or raised; either way file must survive
        finally:
            posted_tracker.json.dump = orig_dump

        after = posted_tracker._load_tracker()
        if "12345" not in after.get("posted", {}):
            fail("failed save destroyed the tracker file (original entry lost)")
        print("[OK ] failed save leaves existing tracker file intact")
    finally:
        posted_tracker.TRACKER_FILE = orig_tracker_file

print("All posted_tracker checks passed.")
