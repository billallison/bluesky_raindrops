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

def remove_toskeet_tag(raindrop_id, access_token):
    """
    Remove the 'toskeet' tag from a Raindrop by first retrieving the existing tags.

    Args:
        raindrop_id: The numeric ID of the Raindrop to update.
        access_token: Raindrop API access token.

    Returns:
        True if the tag was successfully removed, False otherwise.
    """
    # Validate raindrop_id
    if not isinstance(raindrop_id, int):
        logger.error(f"Invalid Raindrop ID (not numeric): {raindrop_id}")
        return False

    get_url = f'https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}'
    update_url = f'https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}'
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        # Fetch current tags on the Raindrop
        response = requests.get(get_url, headers=headers, timeout=10)
        response.raise_for_status()

        raindrop = response.json()
        if 'item' not in raindrop:
            logger.error(f"Failed to fetch Raindrop data. Response: {raindrop}")
            return False

        current_tags = raindrop['item'].get('tags', [])
        logger.info(f"Current tags for Raindrop ID {raindrop_id}: {current_tags}")

        # Check if 'toskeet' is in the tags
        if 'toskeet' in current_tags:
            new_tags = [tag for tag in current_tags if tag != 'toskeet']
            logger.info(f"New tags after removing 'toskeet': {new_tags}")

            # Prepare and send tag update request
            update_data = {
                "tags": new_tags
            }
            update_response = requests.put(update_url, headers=headers, json=update_data, timeout=10)
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