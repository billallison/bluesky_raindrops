# src/bluesky_handler.py

from atproto import Client
from atproto.xrpc_client.models import ids
from atproto.xrpc_client.models import app

import logging

logger = logging.getLogger(__name__)

def post_content_to_bluesky(identifier, password, content, facets, embed):
    client = Client()
    try:
        client.login(identifier, password)
        
        # Upload image if available
        images = []
        if embed:
            with embed['image_file'] as f:
                upload = client.upload_blob(f.read(), embed['mime_type'])
                images.append(app.bsky.embed.images.Image(
                    alt=embed['file_name'],
                    image=upload.blob
                ))
        
        # Create embed
        embed_images = None
        if images:
            embed_images = app.bsky.embed.images.Main(images=images)
        
        # Create post
        post = app.bsky.feed.post.Main(
            text=content,
            facets=facets,
            embed=embed_images
        )
        
        # Send post
        response = client.com.atproto.repo.create_record(
            repo=client.me.did,
            collection=ids.AppBskyFeedPost,
            record=post
        )
        
        logger.info(f"Successfully posted to Bluesky: {response}")
        return True
    except Exception as e:
        logger.error(f"Error posting to Bluesky: {str(e)}")
        return False