import re

def format_bluesky_post_from_raindrop(raindrop):
    title = raindrop.get('title', '')
    link = raindrop.get('link', '')
    note = raindrop.get('note', '')
    
    skeet_content = extract_skeet_content(note)
    
    formatted_post = f"{title}\n\n{link}\n\n{skeet_content}".strip()
    return formatted_post

def extract_skeet_content(note):
    match = re.search(r'\[skeet_content:(.*?)\]', note, re.DOTALL)
    return match.group(1).strip() if match else ''
