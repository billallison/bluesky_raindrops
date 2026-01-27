# src/utils/logging_config.py

import logging
import os

_logging_configured = False

def setup_logging():
    """Configure logging once at application startup.
    
    This should be called once from the main entry point.
    Subsequent calls are no-ops to prevent duplicate handlers.
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # Import here to avoid circular imports
    from src.utils.config import load_config
    
    config = load_config()
    log_level = config['LOG_LEVEL']

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'bluesky_raindrops.log')

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers to prevent duplicates
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    _logging_configured = True


def get_logger(name):
    """Get a logger for the given module name.
    
    Args:
        name: Typically __name__ from the calling module.
        
    Returns:
        A logger instance.
    """
    return logging.getLogger(name)