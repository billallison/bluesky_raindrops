# src/utils/posted_tracker.py
"""
Track successfully posted Raindrop IDs to prevent double-posting.

This provides a safety net when tag removal fails due to transient errors.
The tracker stores posted IDs in a JSON file that persists across runs.
"""

import json
import os
from datetime import datetime, timedelta
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Store in the logs directory alongside the app
TRACKER_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    'logs', 
    'posted_raindrops.json'
)

# Keep records for 7 days before cleanup
RETENTION_DAYS = 7


def _load_tracker() -> dict:
    """Load the tracker file, returning empty dict if not found."""
    try:
        if os.path.exists(TRACKER_FILE):
            with open(TRACKER_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not load tracker file: {e}")
    return {"posted": {}}


def _save_tracker(data: dict) -> None:
    """Save the tracker data to file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
        with open(TRACKER_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        logger.error(f"Could not save tracker file: {e}")


def is_already_posted(raindrop_id: int) -> bool:
    """
    Check if a Raindrop has already been successfully posted.
    
    Args:
        raindrop_id: The Raindrop ID to check.
        
    Returns:
        True if already posted, False otherwise.
    """
    data = _load_tracker()
    posted = data.get("posted", {})
    
    if str(raindrop_id) in posted:
        logger.info(f"Raindrop {raindrop_id} was already posted - skipping to prevent duplicate")
        return True
    return False


def mark_as_posted(raindrop_id: int, bluesky_uri: str | None = None) -> None:
    """
    Record that a Raindrop has been successfully posted.
    
    Args:
        raindrop_id: The Raindrop ID that was posted.
        bluesky_uri: Optional URI of the Bluesky post created.
    """
    data = _load_tracker()
    if "posted" not in data:
        data["posted"] = {}
    
    data["posted"][str(raindrop_id)] = {
        "posted_at": datetime.utcnow().isoformat(),
        "bluesky_uri": bluesky_uri
    }
    
    _save_tracker(data)
    logger.debug(f"Marked Raindrop {raindrop_id} as posted")


def cleanup_old_entries() -> None:
    """Remove entries older than RETENTION_DAYS."""
    data = _load_tracker()
    posted = data.get("posted", {})
    
    if not posted:
        return
    
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    original_count = len(posted)
    
    # Filter out old entries, handling malformed dates gracefully
    new_posted = {}
    for rid, info in posted.items():
        try:
            posted_at_str = info.get("posted_at", "")
            if posted_at_str:
                posted_at = datetime.fromisoformat(posted_at_str)
                if posted_at > cutoff:
                    new_posted[rid] = info
            else:
                # Keep entries without dates (shouldn't happen, but be safe)
                new_posted[rid] = info
        except (ValueError, TypeError) as e:
            # Keep entries with malformed dates rather than losing them
            logger.warning(f"Malformed date for raindrop {rid}, keeping entry: {e}")
            new_posted[rid] = info
    
    data["posted"] = new_posted
    
    removed = original_count - len(data["posted"])
    if removed > 0:
        _save_tracker(data)
        logger.info(f"Cleaned up {removed} old entries from posted tracker")
