# src/raindrop_handler.py

import requests
import json
import logging

logger = logging.getLogger(__name__)

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

    try:
        response = requests.get(
            "https://api.raindrop.io/rest/v1/raindrops/0",
            headers=headers,
            params=params,
            timeout=10
        )
        response.raise_for_status()

        raindrops = response.json().get('items', [])
        if raindrops and '_id' in raindrops[0]:
            logger.info(f"Latest Raindrop with 'toskeet': {raindrops[0]}")
            return raindrops[0]  # Return the entire Raindrop object
        else:
            logger.info("No Raindrops with the 'toskeet' tag found.")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Raindrops: {str(e)}")
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
        # First, get the current tags
        get_url = f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}"
        get_response = requests.get(get_url, headers=headers)
        get_response.raise_for_status()
        
        current_raindrop = get_response.json().get('item', {})
        current_tags = current_raindrop.get('tags', [])
        
        # Remove 'toskeet' from the tags
        if 'toskeet' in current_tags:
            current_tags.remove('toskeet')
            
            # Update the Raindrop with the new tags
            update_url = f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}"
            update_data = {"tags": current_tags}
            update_response = requests.put(update_url, headers=headers, json=update_data)
            update_response.raise_for_status()

            # Parse response for success
            update_result = update_response.json()
            if update_result.get('result', False):
                logger.info(f"'toskeet' tag successfully removed from Raindrop ID {raindrop_id}")
                return True
            else:
                logger.error(f"Failed to update tags for Raindrop ID {raindrop_id}. Response: {update_result}")
        else:
            logger.warning(f"'toskeet' tag not found for Raindrop ID {raindrop_id}. No action taken.")

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error while removing 'toskeet' tag for Raindrop ID {raindrop_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while removing 'toskeet' tag: {str(e)}")

    return False