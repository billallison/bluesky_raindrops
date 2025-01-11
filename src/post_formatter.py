# src/post_formatter.py

import re
import requests
from urllib.parse import urlparse
import io
from PIL import Image

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
        facets.append({
            "index": {"byteStart": start, "byteEnd": end},
            "features": [{"$type": "app.bsky.richtext.facet#link", "uri": link}]
        })

    # Prepare embed for the image
    embed = None
    if cover:
        embed = create_image_embed(cover)
        print(f"Created embed successfully: {embed}")

    return formatted_text, facets, embed

def extract_skeet_content(note):
    match = re.search(r'\[skeet_content:(.*?)\]', note, re.DOTALL)
    return match.group(1).strip() if match else ''

def create_image_embed(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        print(f"Image MIME type: {content_type}")

        if not content_type.startswith('image/'):
            print("Invalid MIME type for image.")
            return None

        image = Image.open(io.BytesIO(response.content))

        # Convert to RGBA if it's not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        # Resize the image to fit Bluesky's dimensions (assuming 1000x1000 max)
        max_size = (1000, 1000)
        image.thumbnail(max_size, Image.LANCZOS)

        # Create a new image with a transparent background
        new_image = Image.new('RGBA', image.size, (0, 0, 0, 0))
        new_image.paste(image, (0, 0), image)

        # Save to BytesIO
        output = io.BytesIO()
        new_image.save(output, format='PNG', optimize=True, quality=85)
        output.seek(0)

        # Check the size of the resized image
        resized_size = output.getbuffer().nbytes
        print(f"Resized image size: {resized_size / 1024:.2f}KB")

        file_name = urlparse(image_url).path.split('/')[-1]
        file_name = f"{file_name.split('.')[0]}.png"

        return {
            'image_file': output,
            'mime_type': 'image/png',
            'file_name': file_name
        }
    except Exception as e:
        print(f"Error creating image embed: {str(e)}")
        return None