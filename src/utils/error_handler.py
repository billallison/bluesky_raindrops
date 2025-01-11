# src/utils/error_handler.py

from src.utils.email_handler import send_error_alert as send_email

def send_error_alert(error_message):
    send_email(error_message)
