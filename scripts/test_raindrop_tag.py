"""Regression test: the trigger tag is configurable (default 'toskeet').

The tag word used to be hard-coded. It is now threaded through
get_latest_raindrop_to_skeet(token, tag=...) and remove_toskeet_tag(token, id, tag=...)
so anyone can adopt the tool with their own tag via the RAINDROP_TAG env var, while
existing deploys that pass nothing keep using 'toskeet'.

Run from the repo root:
    .venv/bin/python scripts/test_raindrop_tag.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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


# --- 1. Custom tag is used in the Raindrop search query ---

def run_search_uses_tag(tag, expected_val):
    captured = {}

    def fake_get(url, headers=None, params=None, timeout=None):
        captured["params"] = params
        return FakeResponse({"items": []})

    orig_get = raindrop_handler.requests.get
    orig_already = raindrop_handler.is_already_posted
    try:
        raindrop_handler.requests.get = fake_get
        raindrop_handler.is_already_posted = lambda rid: False
        if tag is None:
            raindrop_handler.get_latest_raindrop_to_skeet("fake-token")
        else:
            raindrop_handler.get_latest_raindrop_to_skeet("fake-token", tag=tag)
    finally:
        raindrop_handler.requests.get = orig_get
        raindrop_handler.is_already_posted = orig_already

    search = captured.get("params", {}).get("search", "")
    if f'"val": "{expected_val}"' not in search and f'"val":"{expected_val}"' not in search:
        fail(f"search query did not target tag {expected_val!r}; got {search!r}")
    print(f"[OK ] search query targets tag {expected_val!r} (tag arg={tag!r})")


run_search_uses_tag("mytag", "mytag")
run_search_uses_tag(None, "toskeet")  # default preserves backward compatibility


# --- 2. remove_toskeet_tag removes the configured tag, leaving others ---

def run_remove_uses_tag(tag, present_tags, expected_remaining):
    put_body = {}

    def fake_get(url, headers=None, timeout=None):
        return FakeResponse({"item": {"tags": list(present_tags)}})

    def fake_put(url, headers=None, json=None, timeout=None):
        put_body["tags"] = json["tags"]
        return FakeResponse({"result": True})

    orig_get = raindrop_handler.requests.get
    orig_put = raindrop_handler.requests.put
    try:
        raindrop_handler.requests.get = fake_get
        raindrop_handler.requests.put = fake_put
        if tag is None:
            ok = raindrop_handler.remove_toskeet_tag("fake-token", 123)
        else:
            ok = raindrop_handler.remove_toskeet_tag("fake-token", 123, tag=tag)
    finally:
        raindrop_handler.requests.get = orig_get
        raindrop_handler.requests.put = orig_put

    if not ok:
        fail(f"remove_toskeet_tag returned False for tag {tag!r}")
    if put_body.get("tags") != expected_remaining:
        fail(f"expected remaining tags {expected_remaining!r}, got {put_body.get('tags')!r}")
    print(f"[OK ] remove targets tag {tag!r}, leaves {expected_remaining!r}")


run_remove_uses_tag("mytag", ["mytag", "keep"], ["keep"])
run_remove_uses_tag(None, ["toskeet", "keep"], ["keep"])  # default still 'toskeet'

print("All raindrop tag-configurability checks passed.")
