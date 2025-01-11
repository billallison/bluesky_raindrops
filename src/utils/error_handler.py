# src/utils/error_handler.py

import logging
from src.utils.email_handler import send_email

logger = logging.getLogger(__name__)

def send_error_alert(error_message):
    try:
        send_email(error_message)
        logger.info("Error alert email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send error alert email: {str(e)}")