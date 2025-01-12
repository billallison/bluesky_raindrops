# src/utils/email_handler.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.utils.config import load_config
from src.utils.logging_config import setup_logging
import logging
import os

logger = setup_logging()

def get_last_log_entries(num_lines=50):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    log_file = os.path.join(log_dir, 'bluesky_raindrops.log')
    
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-num_lines:])
    except Exception as e:
        logger.error(f"Error reading log file: {str(e)}")
        return "Unable to retrieve log entries."

def send_email(error_message):
    config = load_config()
    
    # Email configuration
    sender_email = config['SMTP_LOGIN']
    receiver_email = config['ADMIN_EMAIL']
    password = config['SMTP_PASSWORD']

    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Error in Bluesky Raindrop Poster"

    # Get the last 50 log entries
    log_entries = get_last_log_entries(50)

    # Add body to email
    body = f"An error occurred in the Bluesky Raindrop Poster:\n\n{error_message}\n\nRecent log entries:\n\n{log_entries}"
    message.attach(MIMEText(body, "plain"))

    # Create SMTP session
    try:
        with smtplib.SMTP_SSL(config['SMTP_SERVER'], config['SMTP_PORT']) as server:
            server.login(sender_email, password)
            server.send_message(message)
        logger.info("Error alert email sent successfully")
    except Exception as e:
        logger.error(f"Failed to send error alert email: {str(e)}")
