# src/utils/error_handler.py

from src.utils.email_handler import send_email
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

def send_error_alert(error_message):
    try:
        send_email(error_message)
    except Exception as e:
        logger.exception(f"Failed to send error alert email: {str(e)}")