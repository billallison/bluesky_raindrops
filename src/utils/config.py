# src/utils/config.py

import os
from dotenv import load_dotenv

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
        'SMTP_PORT'
    ]
    
    config = {}
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f"Missing required environment variable: {var}")
        config[var] = value
    
    # Convert SMTP_PORT to integer
    config['SMTP_PORT'] = int(config['SMTP_PORT'])
    
    return config
