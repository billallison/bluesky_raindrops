# src/post_formatter.py
import re
import requests
import unidecode
import time
import random
import io
from urllib.parse import quote, urlparse
from PIL import Image
import requests
from typing import Dict, Optional, Tuple
from src.utils.logging_config import setup_logging

logger = setup_logging()

USER_AGENTS = [
#    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
#    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
#    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

def format_bluesky_post_from_raindrop(raindrop):
    title = raindrop.get('title', '').strip()
    link = raindrop.get('link', '').strip()
    note = raindrop.get('note', '')
    cover = raindrop.get('cover', '')
  
    description = (raindrop.get('excerpt', '')[:97] + '…').strip()  # Get a short description, limit to 100 characters including ellipsis
    #character limit
    character_limit = 280

    logger.debug(f"Raindrop fields extracted: title={title}, link={link}, cover={cover}, description={description}.")

    skeet_content = extract_skeet_content(note).strip()
    logger.debug(f"Extracted skeet content: {skeet_content}")
 
    # Ensure the URL is properly encoded
    encoded_link = quote(link, safe=':/?=')
    logger.debug(f"Encoded URL: {encoded_link}")

    # Prepare the text content
#    formatted_text = f"{title}\n{skeet_content}\n{encoded_link}"

    # Clean up skeet_content: Strip whitespace and add only if it's non-empty.
    cleaned_skeet_content = skeet_content.strip()

    if cleaned_skeet_content:
        # Only add skeet_content if it's non-empty and trimmed
        formatted_text = f"{title}\n{cleaned_skeet_content}\n{encoded_link}"
        logger.debug(f"cleaned skeet content formatted text: {formatted_text}")
    else:
        # Skip adding an additional line for blank skeet_content
        formatted_text = f"{title}\n{encoded_link}"
        logger.debug(f"blank skeet content formatted text: {formatted_text}")
 

    # Prevent URL truncation
    if len(formatted_text) > character_limit:
        url_start = formatted_text.rfind(encoded_link)
        if url_start != -1:  # Ensure URL is present
            before_url = formatted_text[:url_start]
            truncated_text = truncate_to_graphemes(before_url)  # Truncate text before URL
            formatted_text = truncated_text + " " + encoded_link  # Append URL directly
#            formatted_text = truncated_text + "\n" + encoded_link  # Append URL
        else:
            formatted_text = truncate_to_graphemes(formatted_text)

    logger.debug(f"Truncated formatted text: {formatted_text}")

    # Find the exact position of the URL in the truncated text
# Correct byte computation to align with Bluesky's byte-oriented facets
    url_start = formatted_text.encode('utf-8').find(encoded_link.encode('utf-8'))
    if url_start != -1:
        url_end = url_start + len(encoded_link.encode('utf-8'))  # Byte length of encoded_link
        facets = [{
            "index": {"byteStart": url_start, "byteEnd": url_end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": encoded_link}]
        }]
        logger.debug(f"Facets: {facets}")
    else:
        logger.warning("Encoded link not found (byte-level) in the formatted text!")
        facets = []

    logger.debug(f"Created facets: {facets}")

    # Prepare embed for the image
    embed = None
    if cover:
        embed = create_image_embed(cover, raindrop, timeout=15)
        if embed:
            embed['article_url'] = link
            embed['title'] = title
            embed['description'] = description
        logger.debug(f"Created embed successfully: {embed}")

    return formatted_text, facets, embed

def extract_skeet_content(note):
    match = re.search(r'\[skeet_content:(.*?)\]', note, re.DOTALL)
    return match.group(1).strip() if match else ''

def create_image_embed(image_url, raindrop, timeout=10):
    logger.debug(f"Starting image embedding process for URL: {image_url}")
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    try:
        # First, try to download the image from the original URL
        response = requests.get(image_url, timeout=timeout, headers=headers)
        response.raise_for_status()

        image = Image.open(io.BytesIO(response.content))
        logger.debug(f"Original image opened. Dimensions: {image.width}x{image.height}")

    except Exception as e:
        logger.warning(f"Failed to download or process image from URL: {str(e)}")
        
        # Fallback to the Raindrop cached image
        cache_url = f"https://rdl.ink/render/{urlparse(raindrop['link']).geturl()}"
        logger.info(f"Falling back to Raindrop cached image: {cache_url}")
        try:
            response = requests.get(cache_url, timeout=timeout, headers=headers)
            response.raise_for_status()
            image = Image.open(io.BytesIO(response.content))
            logger.debug(f"Cached image opened. Dimensions: {image.width}x{image.height}")
        except Exception as cache_error:
            logger.error(f"Failed to retrieve cached image: {str(cache_error)}")
            return None

    # Process the image (resize if necessary)
    max_size = (1000, 1000)
    image.thumbnail(max_size)
    logger.debug(f"Image processed. New dimensions: {image.width}x{image.height}")

    # Convert image to RGB
    image = image.convert('RGB')

    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    return {
        'image_file': io.BytesIO(img_byte_arr),
        'alt_text': 'Image from article',
        'mime_type': 'image/jpeg',
        'size': len(img_byte_arr)
    }

def truncate_to_graphemes(text, limit=290):
    """Truncate text to a specified number of graphemes."""
    normalized = unidecode.unidecode(text)
    if len(normalized) <= limit:
        logger.debug(f"Text within limit, no truncation needed: {text[:50]}...")  # Log first 50 chars
        return text

    # Find the last occurrence of http:// or https://
    url_start = max(text.rfind('http://'), text.rfind('https://'))
    
    if url_start != -1:
        url_length = len(text) - url_start
        if url_start + url_length <= limit:
            # URL fits within the limit, truncate only the text before the URL
            truncated = text[:limit - url_length - 3] + '...' + text[url_start:]
        else:
            # URL itself exceeds the limit, truncate the URL
            truncated = text[:limit - 3] + '...'
    else:
        # No URL found, perform normal truncation
        truncated = text[:limit - 3] + '...'
    
    logger.debug(f"Truncated text: {truncated[:50]}...")  # Log first 50 chars of truncated text
    return truncated