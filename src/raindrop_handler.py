# src/raindrop_handler.py

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
    response.raise_for_status()
    
    raindrops = response.json().get('items', [])
    return raindrops[0] if raindrops else None

def remove_toskeet_tag(token, raindrop_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "remove": ["toskeet"]
    }
    response = requests.put(
        f"https://api.raindrop.io/rest/v1/raindrop/{raindrop_id}",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    logger.info(f"Remove tag response: {response.json()}")
    return response.json().get('result', False)