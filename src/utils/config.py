# src/utils/config.py

import os
from dotenv import load_dotenv
import logging

def load_config():
    load_dotenv()
    
    required_vars = [
        'RAINDROP_TOKEN',
        'BLUESKY_IDENTIFIER',
        'BLUESKY_PASSWORD',
        'ADMIN_EMAIL',
        'SMTP_LOGIN',
        'SMTP_PASSWORD',
        'SMTP_SERVER',
        'SMTP_PORT',
        'LOG_LEVEL'
    ]
    
    config = {}
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f"Missing required environment variable: {var}")
        config[var] = value
    
    # Trigger tag is optional — defaults to 'toskeet' so existing deploys need
    # no .env change. Set RAINDROP_TAG to adopt the tool with your own tag.
    config['RAINDROP_TAG'] = os.getenv('RAINDROP_TAG', 'toskeet')

    # Convert SMTP_PORT to integer
    config['SMTP_PORT'] = int(config['SMTP_PORT'])
    
    # Convert LOG_LEVEL to logging level
    config['LOG_LEVEL'] = getattr(logging, config['LOG_LEVEL'].upper(), logging.INFO)
    
    return config