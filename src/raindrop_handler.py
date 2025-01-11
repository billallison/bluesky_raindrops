import requests
import json
import logging

logger = logging.getLogger(__name__)

def get_latest_raindrop_to_skeet(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "search": json.dumps([{"key": "tag", "val": "toskeet"}]),
        "sort": "-created",
        "perpage": 1
    }
    response = requests.get(
        "https://api.raindrop.io/rest/v1/raindrops/0",
        headers=headers,
        params=params
    )
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {str(e)}")
        logger.error(f"Response content: {response.text}")
        raise
    
    raindrops = response.json().get('items', [])
    return raindrops[0] if raindrops else None

def remove_toskeet_tag(token, raindrop_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "tags": ["toskeet"]
    }
    response = requests.put(
        f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}/tags",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    return response.json().get('result', False)
