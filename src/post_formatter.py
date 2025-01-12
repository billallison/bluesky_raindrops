# src/post_formatter.py

import re
import requests
from urllib.parse import urlparse, quote
import io
from PIL import Image
from src.utils.logging_config import setup_logging

logger = setup_logging()

def format_bluesky_post_from_raindrop(raindrop):
    title = raindrop.get('title', '').strip()
    link = raindrop.get('link', '').strip()
    note = raindrop.get('note', '')
    cover = raindrop.get('cover', '')

    skeet_content = extract_skeet_content(note).strip()
 
    # Ensure the URL is properly encoded
    encoded_link = quote(link, safe=':/?=')

     # Adjust the formatting here
    formatted_text = f"{title}\n{skeet_content}\n\n{encoded_link}".strip()
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
        logger.debug(f"Created embed successfully: {embed}")

    return formatted_text, facets, embed

def extract_skeet_content(note):
    match = re.search(r'\[skeet_content:(.*?)\]', note, re.DOTALL)
    return match.group(1).strip() if match else ''

def create_image_embed(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content))
        
        # Convert to PNG
        image = image.convert('RGB')
        
        # Adjust the aspect ratio to 1.91:1
        target_ratio = 1.91
        current_ratio = image.width / image.height
        
        if current_ratio > target_ratio:
            # Image is too wide, crop the width
            new_width = int(image.height * target_ratio)
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, image.height))
        elif current_ratio < target_ratio:
            # Image is too tall, crop the height
            new_height = int(image.width / target_ratio)
            top = (image.height - new_height) // 2
            image = image.crop((0, top, image.width, top + new_height))
        
        # Resize to a suitable size for Bluesky, maintaining 1.91:1 ratio
        max_size = (955, 500)  # 1.91:1 aspect ratio
        image.thumbnail(max_size, Image.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='PNG')
        output.seek(0)
        
        file_name = urlparse(image_url).path.split('/')[-1]
        file_name = f"{file_name.split('.')[0]}.png"
        
        return {
            'image_file': output,
            'mime_type': 'image/png',
            'file_name': file_name,
            'image_url': image_url
        }
    except Exception as e:
        logger.exception(f"Error creating image embed: {str(e)}")
        return None