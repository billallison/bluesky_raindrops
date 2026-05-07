# src/post_formatter.py
"""
Format Raindrop bookmarks for posting to Bluesky.

Uses Bluesky's official 300 grapheme character limit.
Uses atproto's TextBuilder for proper facet (rich text) handling.
"""
import re
import requests
import unicodedata
import random
import io
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from PIL import Image
from atproto import client_utils
from typing import Dict, Optional, Tuple, Any
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Bluesky's official character limit is 300 graphemes (Unicode Grapheme Clusters)
# See: https://docs.bsky.app/docs/advanced-guides/intent-links
BLUESKY_CHAR_LIMIT = 300

# Headroom rebuilds tolerate URL expansion that atproto's TextBuilder applies
# during build_text() (e.g. percent-encoding `&` -> `%26` in display text).
MAX_TRUNCATION_RETRIES = 3

USER_AGENTS = [
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
]

# Query parameters stripped from posted URLs — tracking only, never load-bearing.
# `utm_*` is matched by prefix; everything else is exact-match.
TRACKING_PARAM_PREFIXES = ('utm_',)
TRACKING_PARAM_NAMES = frozenset({
    'cmpid', 'gclid', 'fbclid', 'msclkid', 'dclid', 'yclid',
    'igshid', 'igsh', 'mc_cid', 'mc_eid',
    '_hsenc', '_hsmi', '_hsfp',
    'ocid', 'ncid', 'icid', 'iclid',
    'vero_conv', 'vero_id',
})


def strip_tracking_params(url: str) -> str:
    """Remove common tracking query parameters from a URL.

    Returns the original URL unchanged if parsing fails or there is no query string.
    """
    try:
        parts = urlparse(url)
        if not parts.query:
            return url
        kept = [
            (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
            if not (k.startswith(TRACKING_PARAM_PREFIXES) or k in TRACKING_PARAM_NAMES)
        ]
        new_query = urlencode(kept) if kept else ''
        return urlunparse(parts._replace(query=new_query))
    except Exception as e:
        logger.warning(f"Failed to strip tracking params from {url!r}: {e}")
        return url


def count_graphemes(text: str) -> int:
    """
    Count the number of grapheme clusters in a string.
    
    This is the correct way to count characters for Bluesky's limit,
    as it properly handles emoji and combined characters.
    """
    # Normalize and count grapheme clusters
    count = 0
    i = 0
    while i < len(text):
        # Skip over combining characters
        count += 1
        i += 1
        while i < len(text) and unicodedata.category(text[i]) in ('Mn', 'Mc', 'Me'):
            i += 1
    return count


def truncate_to_grapheme_limit(text: str, limit: int, suffix: str = "…") -> str:
    """
    Truncate text to a specified number of graphemes.
    
    Args:
        text: The text to truncate.
        limit: Maximum number of graphemes.
        suffix: String to append when truncating (default: ellipsis).
        
    Returns:
        Truncated text within the grapheme limit.
    """
    if count_graphemes(text) <= limit:
        return text
    
    # Reserve space for the suffix
    effective_limit = limit - count_graphemes(suffix)
    
    # Build string up to limit
    result = []
    grapheme_count = 0
    i = 0
    
    while i < len(text) and grapheme_count < effective_limit:
        char = text[i]
        result.append(char)
        i += 1
        # Skip combining characters (they're part of the same grapheme)
        while i < len(text) and unicodedata.category(text[i]) in ('Mn', 'Mc', 'Me'):
            result.append(text[i])
            i += 1
        grapheme_count += 1
    
    return ''.join(result) + suffix


def format_bluesky_post_from_raindrop(raindrop: dict) -> Tuple[str, list, Optional[dict]]:
    """
    Format a Raindrop bookmark for posting to Bluesky.
    
    Uses atproto's TextBuilder for proper facet handling.
    Respects Bluesky's 300 grapheme character limit.
    
    Args:
        raindrop: The Raindrop bookmark data.
        
    Returns:
        Tuple of (formatted_text, facets, embed_data)
    """
    title = raindrop.get('title', '').strip()
    raw_link = raindrop.get('link', '').strip()
    link = strip_tracking_params(raw_link)
    if link != raw_link:
        logger.debug(f"Stripped tracking params: {raw_link} -> {link}")
    note = raindrop.get('note', '')
    cover = raindrop.get('cover', '')

    # Get a short description for the embed card (limit to 100 chars including ellipsis)
    excerpt = raindrop.get('excerpt', '').strip()
    description = (excerpt[:97] + '…') if len(excerpt) > 100 else excerpt

    logger.debug(f"Raindrop fields extracted: title={title}, link={link}, cover={cover}")

    skeet_content = extract_skeet_content(note).strip()
    logger.debug(f"Extracted skeet content: {skeet_content}")

    # Build the text portion (title + optional skeet_content)
    full_text = f"{title}\n{skeet_content}" if skeet_content else title

    # Edge case: if the link alone exceeds the limit, just post the link.
    link_display_length = count_graphemes(link)
    if BLUESKY_CHAR_LIMIT - link_display_length - 2 <= 0:
        logger.warning(f"Link is very long ({link_display_length} graphemes), posting link only")
        text_builder = client_utils.TextBuilder()
        text_builder.link(link, link)
        formatted_text = text_builder.build_text()
        facets = text_builder.build_facets()
    else:
        formatted_text, facets = _build_post_with_retries(full_text, link)

    logger.debug(f"Formatted text ({count_graphemes(formatted_text)} graphemes): {formatted_text[:100]}...")
    logger.debug(f"Created facets: {facets}")

    # Prepare embed for the image/link card
    embed = None
    if cover:
        embed = create_image_embed(cover, raindrop, timeout=15)
        if embed:
            embed['article_url'] = link
            embed['title'] = title
            embed['description'] = description
        logger.debug(f"Created embed successfully: {embed is not None}")

    return formatted_text, facets, embed


def _build_post_with_retries(full_text: str, link: str) -> Tuple[str, list]:
    """Build a `body\\nlink` post, re-truncating if the rendered text exceeds the limit.

    `client_utils.TextBuilder` may percent-encode the displayed URL on `build_text()`,
    so the rendered length can exceed our pre-build estimate. After each build we
    measure the actual grapheme count and shrink the body if needed.
    """
    available_for_text = BLUESKY_CHAR_LIMIT - count_graphemes(link) - 2  # -2 for "\n" and ellipsis room
    if count_graphemes(full_text) > available_for_text:
        body_text = truncate_to_grapheme_limit(full_text, available_for_text - 1)
    else:
        body_text = full_text

    formatted_text = ""
    facets: list = []
    for attempt in range(MAX_TRUNCATION_RETRIES):
        tb = client_utils.TextBuilder()
        tb.text(body_text)
        tb.text("\n")
        tb.link(link, link)
        formatted_text = tb.build_text()
        facets = tb.build_facets()

        overage = count_graphemes(formatted_text) - BLUESKY_CHAR_LIMIT
        if overage <= 0:
            return formatted_text, facets

        new_limit = max(count_graphemes(body_text) - overage - 1, 1)
        logger.warning(
            f"Post exceeded limit by {overage} graphemes on attempt {attempt + 1}; "
            f"shrinking body to {new_limit} graphemes and rebuilding"
        )
        body_text = truncate_to_grapheme_limit(body_text, new_limit)

    logger.error(
        f"Post still exceeds limit after {MAX_TRUNCATION_RETRIES} retries; falling back to link-only"
    )
    tb = client_utils.TextBuilder()
    tb.link(link, link)
    return tb.build_text(), tb.build_facets()


def extract_skeet_content(note: str) -> str:
    """Extract custom content from the [skeet_content:...] tag in notes."""
    match = re.search(r'\[skeet_content:(.*?)\]', note, re.DOTALL)
    return match.group(1).strip() if match else ''


def create_image_embed(image_url: str, raindrop: dict, timeout: int = 10) -> Optional[dict]:
    """
    Download and process an image for embedding in a Bluesky post.
    
    Falls back to Raindrop's cached screenshot if the original fails.
    
    Args:
        image_url: URL of the cover image.
        raindrop: The Raindrop data (for fallback URL).
        timeout: Request timeout in seconds.
        
    Returns:
        Dict with image data or None if image processing fails.
    """
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
        
        # Fallback to the Raindrop cached image (note: rdl.ink is undocumented)
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

    # Convert image to RGB (required for JPEG)
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')

    # Convert image to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)
    img_bytes = img_byte_arr.getvalue()

    return {
        'image_file': io.BytesIO(img_bytes),
        'alt_text': 'Image from article',
        'mime_type': 'image/jpeg',
        'size': len(img_bytes)
    }