# src/bluesky_handler.py

from atproto import Client, models
from src.utils.logging_config import setup_logging

logger = setup_logging()

def post_content_to_bluesky(identifier, password, content, facets, embed):
    """
    Post content to Bluesky with optional media embedding and hyperlink facets.
    :param identifier: Bluesky handle or DID.
    :param password: Bluesky account password.
    :param content: Text content for the post.
    :param facets: Rich text facets for clickable links.
    :param embed: Optional embed dictionary (e.g., image metadata).
    :return: Boolean indicating success.
    """
    client = Client()

    try:
        # Log in to the Bluesky client
        client.login(identifier, password)
        logger.info(f"Logged into Bluesky successfully with identifier: {identifier}")

        # Upload the image blob if an embed is provided
        thumb_blob = None
        if embed:
            logger.debug(f"Embed object before upload_blob: {embed}")

            # Ensure image_file is readable and reset pointer
            embed["image_file"].seek(0)

            # Upload the binary image blob to Bluesky without mime_type
            binary_data = embed["image_file"].read()
            logger.debug(f"Binary data size: {len(binary_data)} bytes")
            thumb_blob = client.upload_blob(binary_data)
            logger.info(f"Image uploaded successfully: {thumb_blob}")

        # Prepare the post embed structure if blob was uploaded
        logger.debug("Preparing post embed structure.")
        embed_structure = None
        if embed:
            embed_structure = models.AppBskyEmbedExternal.Main(
                external=models.AppBskyEmbedExternal.External(
                    uri=embed.get("article_url", ""),  # Use .get() with a default value
                    title=embed.get("title", ""),
                    description=embed.get("description", ""),
                    thumb=thumb_blob.blob if thumb_blob else None
                )
            )
        logger.debug(f"Post embed structure: {embed_structure}")

        # Publish the post
        logger.info(f"Posting content to Bluesky: {content[:50]}...")
        response = client.send_post(
            text=content,
            facets=facets,
            embed=embed_structure
        )
        logger.info(f"Successfully posted to Bluesky: {response}")
        return True

    except Exception as e:
        logger.exception(f"Error posting to Bluesky: {str(e)}")
        return False