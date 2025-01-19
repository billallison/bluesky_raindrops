# src/post_formatter.py

import re
import requests
from urllib.parse import urlparse, quote
import io
from PIL import Image
from src.utils.logging_config import setup_logging
import unidecode

logger = setup_logging()

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

     # Adjust the formatting here
    formatted_text = f"{title}\n\n{skeet_content}\n\n{encoded_link}".strip()
    formatted_text = truncate_to_graphemes(formatted_text)
    logger.debug(f"Formatted text: {formatted_text}")

    # Create facets for the URL
    facets = []
    # Find the last occurrence of the encoded link
    link_start = formatted_text.rfind(encoded_link)
    if link_start != -1:
        link_end = link_start + len(encoded_link)
        facets.append({
            "index": {
                "byteStart": len(formatted_text[:link_start].encode('utf-8')),
                "byteEnd": len(formatted_text[:link_end].encode('utf-8'))
            },
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": encoded_link}]
        })

    # Prepare embed for the image
    embed = None
    if cover:
        embed = create_image_embed(cover)
        if embed:
            embed['article_url'] = link
            embed['title'] = title
            embed['description'] = description
        logger.debug(f"Created embed successfully: {embed}")

    return formatted_text, facets, embed

def extract_skeet_content(note):
    match = re.search(r'\[skeet_content:(.*?)\]', note, re.DOTALL)
    return match.group(1).strip() if match else ''

def create_image_embed(image_url):
    logger.debug(f"Starting image embedding process for URL: {image_url}")

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        logger.debug(f"Image downloaded successfully: size={len(response.content)} bytes")

        image = Image.open(io.BytesIO(response.content))
        logger.debug(f"Image opened. Original dimensions: {image.width}x{image.height}")

        # Calculate new dimensions
        max_width = 1000
        max_height = 1000
        width, height = image.size
        
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            image = image.resize((new_width, new_height))
        else:
            new_width, new_height = width, height

        logger.debug(f"Image cropped and resized: {new_width}x{new_height}")

        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Save to BytesIO object
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        return {
            'image_file': img_byte_arr,
            'alt_text': 'Image from article'
        }

    except Exception as e:
        logger.exception(f"Error creating image embed: {str(e)}")
        return None

def truncate_to_graphemes(text, limit=300):
    """Truncate text to a specified number of graphemes."""
    normalized = unidecode.unidecode(text)
    if len(normalized) <= limit:
        return text
    return text[:limit - 3] + '...'