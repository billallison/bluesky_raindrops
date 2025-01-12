# src/utils/error_handler.py

from src.utils.email_handler import send_email
from src.utils.logging_config import setup_logging

logger = setup_logging()

def send_error_alert(error_message):
    try:
        send_email(error_message)
        logger.info("Error alert email sent successfully")
    except Exception as e:
        logger.exception(f"Failed to send error alert email: {str(e)}")