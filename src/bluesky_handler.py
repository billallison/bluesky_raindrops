# src/bluesky_handler.py

from atproto import Client, models
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
                upload = client.upload_blob(f.read())  # Changed this line
                images.append(models.AppBskyEmbedImages.Image(alt=embed['file_name'], image=upload))
        
        # Create embed
        embed_images = None
        if images:
            embed_images = models.AppBskyEmbedImages.Main(images=images)
        
        # Send post
        response = client.com.atproto.repo.create_record(
            repo=client.me.did,
            collection='app.bsky.feed.post',
            record=models.AppBskyFeedPost.Main(
                text=content,
                facets=facets,
                embed=embed_images
            )
        )
        
        logger.info(f"Successfully posted to Bluesky: {response}")
        return True
    except Exception as e:
        logger.error(f"Error posting to Bluesky: {str(e)}")
        return False