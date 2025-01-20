import re
import requests
from urllib.parse import urlparse, quote
import io
from PIL import Image
from src.utils.logging_config import setup_logging
import unidecode
import time
import random

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
    description = raindrop.get('excerpt', '')[:100]  # Get a short description, limit to 100 characters

    logger.debug(f"Raindrop fields extracted: title={title}, link={link}, cover={cover}, description={description}.")

    skeet_content = extract_skeet_content(note).strip()
    logger.debug(f"Extracted skeet content: {skeet_content}")
 
    # Ensure the URL is properly encoded
    encoded_link = quote(link, safe=':/?=')
    logger.debug(f"Encoded URL: {encoded_link}")

    # Prepare the text content
    formatted_text = f"{title}\n{skeet_content}\n{encoded_link}"
    formatted_text = truncate_to_graphemes(formatted_text)
    logger.debug(f"Formatted text: {formatted_text}")

    # Prepare the facet for the hyperlink
    #facets = [{
    #    "index": {"byteStart": len(title) + len(skeet_content) + 2, "byteEnd": len(formatted_text)},
    #    "features": [{"$type": "app.bsky.richtext.facet#link", "uri": encoded_link}]
    #}]
    
    # Ensure the URL is properly encoded
    encoded_link = quote(link, safe=':/?=')

    # Prepare the text content
    formatted_text = f"{title}\n{skeet_content}\n{encoded_link}"

    # Calculate the correct byte indices for the URL
    url_start = len(title) + len(skeet_content) + 2  # +2 for the two newline characters
    url_end = len(formatted_text)

    # Create the facet for the hyperlink
    facets = [{
        "index": {"byteStart": url_start, "byteEnd": url_end},
        "features": [{"$type": "app.bsky.richtext.facet#link", "uri": encoded_link}]
    }]

    # Ensure the formatted text is within the character limit
    formatted_text = truncate_to_graphemes(formatted_text)
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

def truncate_to_graphemes(text, limit=300):
    """Truncate text to a specified number of graphemes."""
    normalized = unidecode.unidecode(text)
    if len(normalized) <= limit:
        return text
    return text[:limit - 3] + '...'