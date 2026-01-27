# Changelog

## [1.1.0] - 2026-01-26

### Bug Fixes

- **Double-posting prevention**: Posts no longer duplicate when Raindrop API returns 502 during tag removal
  - Added local tracking of posted items (`posted_tracker.py`)
  - Items marked as posted BEFORE attempting tag removal
  - Retry logic with exponential backoff for transient API errors

- **Character limit correction**: Fixed post truncation using correct 300 grapheme limit (was incorrectly using 280/290)
  - Proper Unicode grapheme cluster counting
  - Posts now use full Bluesky character allowance

### New Features

- **File locking**: Prevents concurrent script execution from overlapping cron jobs
  - PID-based lock with stale lock detection
  - Automatic cleanup of orphaned locks

- **Posted item tracking**: JSON-based tracking with 7-day retention
  - Survives tag removal failures
  - Automatic cleanup of old entries

### Improvements

- **TextBuilder migration**: Switched to atproto's `TextBuilder` for facet handling
  - Eliminates manual byte-offset calculations
  - More reliable link detection and formatting

- **Retry logic**: Added retry with exponential backoff for transient errors
  - Handles 502, 503, 504, 429 status codes
  - Handles connection timeouts
  - Fresh client session on each retry attempt

- **Logging centralization**: Refactored to use single `setup_logging()` call
  - All modules use `get_logger(name)` for consistent logging
  - Prevents duplicate log entries

### Technical Details

**Files Added:**
- `src/utils/posted_tracker.py` - Track posted Raindrop IDs
- `src/utils/file_lock.py` - Script-level locking

**Files Modified:**
- `raindrop_to_bluesky.py` - Integrated tracking and locking
- `src/raindrop_handler.py` - Added retry logic, tracking checks
- `src/bluesky_handler.py` - Added retry logic, fresh client per attempt
- `src/post_formatter.py` - Complete rewrite with TextBuilder
- `src/utils/logging_config.py` - Centralized setup
- `src/utils/error_handler.py` - Use get_logger
- `src/utils/email_handler.py` - Use get_logger
