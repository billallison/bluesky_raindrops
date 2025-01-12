# raindrop_to_bluesky.py

from src.raindrop_handler import get_latest_raindrop_to_skeet, remove_toskeet_tag
from src.bluesky_handler import post_content_to_bluesky
from src.post_formatter import format_bluesky_post_from_raindrop
from src.utils.error_handler import send_error_alert
from src.utils.config import load_config
from src.utils.logging_config import setup_logging

logger = setup_logging()

def main():
    config = load_config()
    
    try:
        raindrop = get_latest_raindrop_to_skeet(config['RAINDROP_TOKEN'])
        if raindrop:
            post_content, facets, embed = format_bluesky_post_from_raindrop(raindrop)
            success = post_content_to_bluesky(
                config['BLUESKY_IDENTIFIER'],
                config['BLUESKY_PASSWORD'],
                post_content,
                facets,
                embed
            )
            if success:
                logger.info("Successfully posted to Bluesky")
                if remove_toskeet_tag(config['RAINDROP_TOKEN'], raindrop['_id']):
                    logger.info("Removed 'toskeet' tag from Raindrop")
                else:
                    error_msg = "Failed to remove 'toskeet' tag from Raindrop"
                    logger.error(error_msg)
                    send_error_alert(error_msg)
            else:
                error_msg = "Failed to post to Bluesky"
                logger.error(error_msg)
                send_error_alert(error_msg)
        else:
            logger.info("No new content to post")
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        logger.exception(error_msg)
        send_error_alert(error_msg)

if __name__ == "__main__":
    main()