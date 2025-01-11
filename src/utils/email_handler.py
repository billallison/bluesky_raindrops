# src/utils/email_handler.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.utils.config import load_config

def send_email(error_message):  # Changed function name from send_error_alert to send_email
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

    # Add body to email
    body = f"An error occurred in the Bluesky Raindrop Poster:\n\n{error_message}"
    message.attach(MIMEText(body, "plain"))

    # Create SMTP session
    try:
        with smtplib.SMTP_SSL(config['SMTP_SERVER'], config['SMTP_PORT']) as server:
            server.login(sender_email, password)
            server.send_message(message)
        print("Error alert email sent successfully")
    except Exception as e:
        print(f"Failed to send error alert email: {str(e)}")