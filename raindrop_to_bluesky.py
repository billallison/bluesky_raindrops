# raindrop_to_bluesky.py

from src.raindrop_handler import get_latest_raindrop_to_skeet, remove_toskeet_tag
from src.bluesky_handler import post_content_to_bluesky
from src.post_formatter import format_bluesky_post_from_raindrop
from src.utils.error_handler import send_error_alert
from src.utils.config import load_config
from src.utils.logging_config import setup_logging, get_logger
from src.utils.posted_tracker import mark_as_posted, cleanup_old_entries
from src.utils.file_lock import script_lock

# Initialize logging once at startup
setup_logging()
logger = get_logger(__name__)


def main():
    config = load_config()
    
    # Cleanup old entries from the posted tracker periodically
    cleanup_old_entries()
    
    try:
        raindrop = get_latest_raindrop_to_skeet(config['RAINDROP_TOKEN'])
        if raindrop:
            raindrop_id = raindrop['_id']
            formatted_text, facets, embed = format_bluesky_post_from_raindrop(raindrop)
            logger.debug(f"Embed structure before posting: {embed}")
            
            result = post_content_to_bluesky(
                config['BLUESKY_IDENTIFIER'],
                config['BLUESKY_PASSWORD'],
                formatted_text,
                facets,
                embed
            )
            
            if result:
                # Extract the Bluesky post URI if available
                bluesky_uri = result.uri if hasattr(result, 'uri') else str(result)
                logger.info(f"Successfully posted to Bluesky: {bluesky_uri}")
                
                # IMPORTANT: Mark as posted BEFORE attempting tag removal
                # This prevents double-posting even if tag removal fails
                mark_as_posted(raindrop_id, bluesky_uri)
                
                if remove_toskeet_tag(config['RAINDROP_TOKEN'], raindrop_id):
                    logger.info("Removed 'toskeet' tag from Raindrop")
                else:
                    # Tag removal failed, but post is tracked - won't double-post
                    error_msg = f"Failed to remove 'toskeet' tag from Raindrop {raindrop_id}. Post was successful and tracked - will not double-post."
                    logger.warning(error_msg)
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
    with script_lock() as acquired:
        if not acquired:
            logger.warning("Another instance is already running - exiting")
        else:
            try:
                main()
            except Exception as e:
                logger.exception(f"Unexpected error occurred in main script: {str(e)}")
