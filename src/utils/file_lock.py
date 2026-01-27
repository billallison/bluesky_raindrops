# src/utils/file_lock.py
"""
Simple file-based lock to prevent concurrent script execution.

Uses a lock file with the PID of the running process. Stale locks
(from crashed processes) are automatically detected and cleaned up.
"""

import os
import sys
import time
from contextlib import contextmanager
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Lock file location (in logs directory)
LOCK_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'logs',
    'raindrop_bot.lock'
)

# Maximum age of a lock file before considering it stale (seconds)
# Set to 10 minutes - longer than any reasonable run
STALE_LOCK_SECONDS = 600


def _is_process_running(pid: int) -> bool:
    """Check if a process with the given PID is still running."""
    try:
        os.kill(pid, 0)  # Signal 0 doesn't kill, just checks
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_lock() -> tuple[int | None, float | None]:
    """Read the lock file and return (pid, timestamp) or (None, None)."""
    try:
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    parts = content.split(':')
                    if len(parts) == 2:
                        return int(parts[0]), float(parts[1])
    except (ValueError, IOError) as e:
        logger.warning(f"Could not read lock file: {e}")
    return None, None


def _write_lock() -> bool:
    """Write current PID and timestamp to lock file."""
    try:
        os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
        with open(LOCK_FILE, 'w') as f:
            f.write(f"{os.getpid()}:{time.time()}")
        return True
    except IOError as e:
        logger.error(f"Could not write lock file: {e}")
        return False


def _remove_lock() -> None:
    """Remove the lock file."""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except IOError as e:
        logger.warning(f"Could not remove lock file: {e}")


def acquire_lock() -> bool:
    """
    Attempt to acquire the lock.
    
    Returns:
        True if lock acquired, False if another instance is running.
    """
    pid, timestamp = _read_lock()
    
    if pid is not None:
        # Check if the lock is stale
        lock_age = time.time() - (timestamp or 0)
        
        if lock_age > STALE_LOCK_SECONDS:
            logger.warning(f"Found stale lock (age: {lock_age:.0f}s), removing it")
            _remove_lock()
        elif _is_process_running(pid):
            logger.warning(f"Another instance is already running (PID: {pid})")
            return False
        else:
            logger.warning(f"Found orphaned lock from dead process (PID: {pid}), removing it")
            _remove_lock()
    
    return _write_lock()


def release_lock() -> None:
    """Release the lock (remove the lock file)."""
    _remove_lock()
    logger.debug("Lock released")


@contextmanager
def script_lock():
    """
    Context manager for script locking.
    
    Usage:
        with script_lock() as acquired:
            if not acquired:
                return  # Another instance is running
            # ... do work ...
    """
    acquired = acquire_lock()
    try:
        yield acquired
    finally:
        if acquired:
            release_lock()
