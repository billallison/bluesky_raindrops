# src/bluesky_handler.py

from atproto import Client
import logging

logger = logging.getLogger(__name__)

def post_content_to_bluesky(identifier, password, content):
    client = Client()
    try:
        client.login(identifier, password)
        
        response = client.send_post(text=content)
        
        logger.info(f"Successfully posted to Bluesky: {response}")
        return True
    except Exception as e:
        logger.error(f"Error posting to Bluesky: {str(e)}")
        return False