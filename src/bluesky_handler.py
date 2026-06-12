# src/bluesky_handler.py
"""
Handle posting content to Bluesky via the AT Protocol.

Includes retry logic for transient failures and proper timeout handling.
"""
import time
from atproto import Client, models
from atproto_client.exceptions import InvokeTimeoutError, RequestException
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2  # Base delay, will use exponential backoff

# HTTP status codes worth retrying
TRANSIENT_STATUS_CODES = (429, 502, 503, 504)


def _is_transient_request_error(e) -> bool:
    """Decide retryability from the response status code, not str(e) —
    substring matching false-positives on codes appearing in error bodies."""
    response = getattr(e, 'response', None)
    status_code = getattr(response, 'status_code', None)
    if status_code is not None:
        return status_code in TRANSIENT_STATUS_CODES
    # No response attached (network-level failure) — fall back to text match
    return any(code in str(e) for code in ('502', '503', '504', '429', 'timeout'))


def post_content_to_bluesky(identifier, password, content, facets, embed):
    """
    Post content to Bluesky with optional media embedding and hyperlink facets.
    
    Includes retry logic with exponential backoff for transient failures.
    
    Args:
        identifier: Bluesky handle or DID.
        password: Bluesky account password (app password recommended).
        content: Text content for the post.
        facets: Rich text facets for clickable links (from TextBuilder).
        embed: Optional embed dictionary (e.g., image metadata).
        
    Returns:
        Post response object on success, None on failure.
    """
    
    for attempt in range(MAX_RETRIES):
        try:
            # Create fresh client for each attempt (session may be stale after timeout)
            client = Client()
            
            # Log in to the Bluesky client
            client.login(identifier, password)
            logger.info(f"Logged into Bluesky successfully with identifier: {identifier}")

            # Upload the image blob if an embed is provided
            thumb_blob = None
            if embed:
                logger.debug(f"Embed object before upload_blob: {embed}")
                # Ensure image_file is readable and reset pointer (important for retries)
                if hasattr(embed.get("image_file"), 'seek'):
                    embed["image_file"].seek(0)
                binary_data = embed["image_file"].read()
                logger.debug(f"Binary data size: {len(binary_data)} bytes")
                thumb_blob = client.upload_blob(binary_data)
                logger.info(f"Image uploaded successfully: {thumb_blob}")

            # Prepare the post embed structure if a blob was uploaded
            embed_structure = None
            if embed and thumb_blob:
                try:
                    embed_structure = models.AppBskyEmbedExternal.Main(
                        external=models.AppBskyEmbedExternal.External(
                            uri=embed["article_url"],
                            title=embed["title"],
                            description=embed["description"],
                            thumb=thumb_blob.blob
                        )
                    )
                    logger.debug(f"Post embed structure created: {embed_structure}")
                except AttributeError as e:
                    logger.error(f"Error creating embed structure: {e}")
                    # Continue without embed rather than failing completely
                    embed_structure = None

            # Publish the post with facets (for the clickable hyperlink)
            logger.info(f"Posting content to Bluesky: {content[:100]}...")
            response = client.send_post(
                text=content,
                facets=facets,
                embed=embed_structure
            )
            logger.info(f"Successfully posted to Bluesky: {response}")
            return response  # Return the response object (contains URI, CID)

        except InvokeTimeoutError as e:
            delay = RETRY_DELAY_SECONDS * (2 ** attempt)
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"Timeout posting to Bluesky (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
                continue
            else:
                logger.exception(f"Timeout posting to Bluesky after {MAX_RETRIES} attempts: {str(e)}")
                return None
                
        except RequestException as e:
            # Check if this is a transient error worth retrying
            delay = RETRY_DELAY_SECONDS * (2 ** attempt)
            is_transient = _is_transient_request_error(e)
            
            if is_transient and attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"Transient error posting to Bluesky (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
                continue
            else:
                logger.exception(f"Error posting to Bluesky: {str(e)}")
                return None
                
        except Exception as e:
            logger.exception(f"Unexpected error posting to Bluesky: {str(e)}")
            return None

    return None