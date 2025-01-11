# src/post_formatter.py

import re
from atproto import models
import requests
from urllib.parse import urlparse
import io

def format_bluesky_post_from_raindrop(raindrop):
    title = raindrop.get('title', '')
    link = raindrop.get('link', '')
    note = raindrop.get('note', '')
    cover = raindrop.get('cover', '')  # Get the cover image URL from Raindrop
    
    skeet_content = extract_skeet_content(note)
    
    formatted_text = f"{title}\n\n{skeet_content}\n\n{link}".strip()
    
    # Create facets for the URL
    facets = []
    url_match = re.search(re.escape(link), formatted_text)
    if url_match:
        start, end = url_match.span()
        facets.append(models.AppBskyRichtextFacet.Main(
            index=models.AppBskyRichtextFacet.ByteSlice(byteStart=start, byteEnd=end),
            features=[models.AppBskyRichtextFacet.Link(uri=link)]
        ))
    
    # Prepare embed for the image
    embed = None
    if cover:
        embed = create_image_embed(cover)
    
    return formatted_text, facets, embed

def extract_skeet_content(note):
    match = re.search(r'\[skeet_content:(.*?)\]', note, re.DOTALL)
    return match.group(1).strip() if match else ''

def create_image_embed(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return None
        
        file_name = urlparse(image_url).path.split('/')[-1]
        
        # Create a file-like object from the image content
        image_file = io.BytesIO(response.content)
        
        return {
            'image_file': image_file,
            'mime_type': content_type,
            'file_name': file_name
        }
    except Exception as e:
        print(f"Error creating image embed: {str(e)}")
        return None