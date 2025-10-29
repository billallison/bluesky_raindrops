# src/raindrop_handler.py

import requests
import json
from src.utils.logging_config import setup_logging

logger = setup_logging()

def get_latest_raindrop_to_skeet(token):
    """
    Get the latest Raindrop with the 'toskeet' tag.
    Args:
        token: API Bearer token for authentication.
    Returns:
        The latest Raindrop object or None if not found.
    """
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "search": json.dumps([{"key": "tag", "val": "toskeet"}]),
        "sort": "-created",
        "perpage": 1
    }

    logger.debug(f"Requesting latest Raindrop with 'toskeet' tag. Params: {params}")


    try:
        response = requests.get(
            "https://api.raindrop.io/rest/v1/raindrops/0",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()
        
        # Log response content for debugging
        logger.debug(f"Response from Raindrop API: {response.text}")

        raindrops = response.json().get('items', [])
        if raindrops and '_id' in raindrops[0]:
            logger.info(f"Latest Raindrop with 'toskeet': {raindrops[0]}")
            return raindrops[0]  # Return the entire Raindrop object
        else:
            logger.info("No Raindrops with the 'toskeet' tag found.")
            return None

    except requests.exceptions.RequestException as e:
        logger.exception(f"Error fetching Raindrops: {str(e)}")
        return None

def remove_toskeet_tag(access_token, raindrop_id):
    """
    Remove the 'toskeet' tag from a Raindrop by first retrieving the existing tags.

    Args:
        access_token: Raindrop API access token.
        raindrop_id: The numeric ID of the Raindrop to update.
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    try:
        # First, get the current Raindrop data
        logger.debug(f"Fetching current tags for Raindrop ID {raindrop_id}")
        get_url = f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}"
        get_response = requests.get(get_url, headers=headers, timeout=10)
        get_response.raise_for_status()
        raindrop_data = get_response.json().get('item', {})

        # Extract current tags
        current_tags = raindrop_data.get('tags', [])
        logger.info(f"Current tags for Raindrop ID {raindrop_id}: {current_tags}")

        # Remove 'toskeet' tag if present
        if 'toskeet' in current_tags:
            current_tags.remove('toskeet')
            logger.info(f"Removing 'toskeet' tag from Raindrop ID {raindrop_id}. New tags: {current_tags}")

            # Update the Raindrop with the new tag list
            update_url = f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}"
            update_data = {"tags": current_tags}
            update_response = requests.put(update_url, headers=headers, json=update_data, timeout=10)
            update_response.raise_for_status()

            # Parse response for success
            update_result = update_response.json()
            logger.debug(f"Tag removal API response: {update_result}")
            if update_result.get('result', False):
                logger.info(f"'toskeet' tag successfully removed from Raindrop ID {raindrop_id}")
                return True
            else:
                logger.error(f"Failed to update tags for Raindrop ID {raindrop_id}. Response: {update_result}")
                return False
        else:
            # Tag already removed - this is success, not an error
            logger.info(f"'toskeet' tag already removed from Raindrop ID {raindrop_id}. No action needed.")
            return True

    except requests.exceptions.RequestException as e:
        logger.exception(f"HTTP error while removing 'toskeet' tag for Raindrop ID {raindrop_id}: {str(e)}")
    except Exception as e:
        logger.exception(f"Unexpected error while removing 'toskeet' tag: {str(e)}")

    return False