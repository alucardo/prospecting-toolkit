# Domeny social media i platform ktore nie nadaja sie do scrapowania
BLOCKED_SCRAPING_DOMAINS = [
    # Meta
    'facebook.com', 'fb.com', 'fb.me', 'instagram.com',
    # Google
    'youtube.com', 'youtu.be',
    # Microsoft
    'linkedin.com',
    # Twitter / X
    'twitter.com', 'x.com',
    # TikTok
    'tiktok.com',
    # Pinterest
    'pinterest.com', 'pin.it',
    # Snapchat
    'snapchat.com',
    # Reddit
    'reddit.com',
    # Inne
    'vk.com', 'tumblr.com', 'flickr.com', 'tripadvisor.com',
]


def is_blocked_for_scraping(url):
    """Zwraca True jesli URL nalezy do platformy ktorej nie mozna scrapowac."""
    if not url:
        return False
    return any(domain in url for domain in BLOCKED_SCRAPING_DOMAINS)
