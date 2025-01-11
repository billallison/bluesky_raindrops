# main.py

import logging
from src.raindrop_handler import get_latest_raindrop_to_skeet, remove_toskeet_tag
from src.bluesky_handler import post_content_to_bluesky
from src.post_formatter import format_bluesky_post_from_raindrop
from src.utils.error_handler import send_error_alert
from src.utils.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    config = load_config()
    
    try:
        raindrop = get_latest_raindrop_to_skeet(config['RAINDROP_TOKEN'])
        if raindrop:
            post_content = format_bluesky_post_from_raindrop(raindrop)
            success = post_content_to_bluesky(
                config['BLUESKY_IDENTIFIER'],
                config['BLUESKY_PASSWORD'],
                post_content
            )
            if success:
                logger.info("Successfully posted to Bluesky")
                remove_toskeet_tag(config['RAINDROP_TOKEN'], raindrop['_id'])
                logger.info("Removed 'toskeet' tag from Raindrop")
            else:
                logger.error("Failed to post to Bluesky")
        else:
            logger.info("No new content to post")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        send_error_alert(str(e))

if __name__ == "__main__":
    main()