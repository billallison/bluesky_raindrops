# src/bluesky_handler.py

from bsky import BskyAgent
import logging

logger = logging.getLogger(__name__)

def post_content_to_bluesky(identifier, password, content):
    agent = BskyAgent(service="https://bsky.social")
    
    try:
        agent.login(identifier, password)
        
        response = agent.post(text=content)
        
        logger.info(f"Successfully posted to Bluesky: {response}")
        return True
    except Exception as e:
        logger.error(f"Error posting to Bluesky: {str(e)}")
        return False