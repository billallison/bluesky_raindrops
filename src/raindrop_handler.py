# src/raindrop_handler.py

import requests
import json
import time
from src.utils.logging_config import get_logger
from src.utils.posted_tracker import is_already_posted

logger = get_logger(__name__)

# Retry configuration for transient failures
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2  # Base delay, will use exponential backoff


def get_latest_raindrop_to_skeet(token, tag="toskeet"):
    """
    Get the latest Raindrop with the trigger tag (default 'toskeet').

    Filters out items that have already been posted (tracked locally)
    to prevent double-posting when tag removal fails.

    Args:
        token: API Bearer token for authentication.
        tag: The trigger tag to search for (default 'toskeet').
    Returns:
        The latest Raindrop object or None if not found.
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "search": json.dumps([{"key": "tag", "val": tag}]),
        "sort": "-created",
        "perpage": 5  # Fetch a few in case some are already posted
    }

    logger.debug(f"Requesting latest Raindrop with '{tag}' tag. Params: {params}")

    try:
        response = requests.get(
            "https://api.raindrop.io/rest/v1/raindrops/0",
            headers=headers,
            params=params,
            timeout=15
        )
        response.raise_for_status()
        
        # Log response content for debugging
        logger.debug(f"Response from Raindrop API: {response.text}")

        raindrops = response.json().get('items', [])
        
        # Find the first raindrop that hasn't been posted yet
        for raindrop in raindrops:
            if '_id' in raindrop:
                raindrop_id = raindrop['_id']
                
                # Check if already posted (safety net for failed tag removal)
                if is_already_posted(raindrop_id):
                    logger.info(f"Skipping Raindrop {raindrop_id} - already posted previously")
                    # The tag is still present (or it wouldn't be in this fetch),
                    # so a previous removal failed — retry it now (self-healing).
                    try:
                        if remove_toskeet_tag(token, raindrop_id, tag=tag):
                            logger.info(f"Self-healed: removed stuck '{tag}' tag from Raindrop {raindrop_id}")
                        else:
                            logger.warning(f"Retry of '{tag}' tag removal failed for Raindrop {raindrop_id}")
                    except Exception:
                        logger.exception(f"Error retrying tag removal for Raindrop {raindrop_id}")
                    continue

                logger.info(f"Latest Raindrop with '{tag}': {raindrop}")
                return raindrop

        logger.info(f"No Raindrops with the '{tag}' tag found.")
        return None

    except requests.exceptions.RequestException as e:
        logger.exception(f"Error fetching Raindrops: {str(e)}")
        return None


def remove_toskeet_tag(access_token, raindrop_id, tag="toskeet"):
    """
    Remove the trigger tag (default 'toskeet') from a Raindrop by first
    retrieving the existing tags.

    Includes retry logic with exponential backoff for transient failures.

    Args:
        access_token: Raindrop API access token.
        raindrop_id: The numeric ID of the Raindrop to update.
        tag: The trigger tag to remove (default 'toskeet').

    Returns:
        True if tag was successfully removed, False otherwise.
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    for attempt in range(MAX_RETRIES):
        try:
            # First, get the current Raindrop data
            logger.debug(f"Fetching current tags for Raindrop ID {raindrop_id} (attempt {attempt + 1}/{MAX_RETRIES})")
            get_url = f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}"
            get_response = requests.get(get_url, headers=headers, timeout=15)
            get_response.raise_for_status()
            raindrop_data = get_response.json().get('item', {})

            # Extract current tags
            current_tags = raindrop_data.get('tags', [])
            logger.info(f"Current tags for Raindrop ID {raindrop_id}: {current_tags}")

            # Remove the trigger tag if present
            if tag in current_tags:
                current_tags.remove(tag)
                logger.info(f"Removing '{tag}' tag from Raindrop ID {raindrop_id}. New tags: {current_tags}")

                # Update the Raindrop with the new tag list
                update_url = f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}"
                update_data = {"tags": current_tags}
                update_response = requests.put(update_url, headers=headers, json=update_data, timeout=15)
                update_response.raise_for_status()

                # Parse response for success
                update_result = update_response.json()
                logger.debug(f"Tag removal API response: {update_result}")
                if update_result.get('result', False):
                    logger.info(f"'{tag}' tag successfully removed from Raindrop ID {raindrop_id}")
                    return True
                else:
                    logger.error(f"Failed to update tags for Raindrop ID {raindrop_id}. Response: {update_result}")
                    return False
            else:
                # Tag already removed - this is success, not an error
                logger.info(f"'{tag}' tag already removed from Raindrop ID {raindrop_id}. No action needed.")
                return True

        except requests.exceptions.RequestException as e:
            delay = RETRY_DELAY_SECONDS * (2 ** attempt)  # Exponential backoff
            
            # Check if this is a transient error worth retrying
            is_transient = (
                isinstance(e, requests.exceptions.Timeout) or
                (hasattr(e, 'response') and e.response is not None and 
                 e.response.status_code in (502, 503, 504, 429))
            )
            
            if is_transient and attempt < MAX_RETRIES - 1:
                logger.warning(
                    f"Transient error removing tag (attempt {attempt + 1}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)
                continue
            else:
                logger.exception(f"HTTP error while removing '{tag}' tag for Raindrop ID {raindrop_id}: {str(e)}")
                return False

        except Exception as e:
            logger.exception(f"Unexpected error while removing '{tag}' tag: {str(e)}")
            return False

    return False