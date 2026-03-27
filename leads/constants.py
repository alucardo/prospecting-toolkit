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


# Mapa polskich nazw województw → location_code DataForSEO
# Kody pobrane z: GET /v3/keywords_data/google_ads/locations/pl
# Endpoint: keywords_data/google_ads/search_volume/live wymaga location_code (int)
VOIVODESHIP_LOCATION_CODE_MAP = {
    'dolnośląskie':        20847,  # Lower Silesian Voivodeship
    'kujawsko-pomorskie': 20848,  # Kuyavian-Pomeranian Voivodeship
    'lubelskie':          20851,  # Lublin Voivodeship
    'lubuskie':           20849,  # Lubusz Voivodeship
    'łódzkie':             20850,  # Lodz Voivodeship
    'małopolskie':        20852,  # Lesser Poland Voivodeship
    'mazowieckie':        20853,  # Masovian Voivodeship
    'opolskie':           20854,  # Opole Voivodeship
    'podkarpackie':       20856,  # Podkarpackie Voivodeship
    'podlaskie':          20855,  # Podlaskie Voivodeship
    'pomorskie':          20857,  # Pomeranian Voivodeship
    'śląskie':             20859,  # Silesian Voivodeship
    'świętokrzyskie':      20858,  # Swietokrzyskie Voivodeship
    'warmińsko-mazurskie': 20860,  # Warmian-Masurian Voivodeship
    'wielkopolskie':      20861,  # Greater Poland Voivodeship
    'zachodniopomorskie': 20862,  # West Pomeranian Voivodeship
}

POLAND_LOCATION_CODE = 2616  # fallback: cała Polska


def get_dataforseo_location_code(voivodeship_name):
    """
    Zwraca location_code DataForSEO na podstawie polskiej nazwy województwa.
    Porównuje bez względu na wielkość liter i białe znaki.
    Fallback: 2616 (cała Polska) jeśli nie znaleziono.
    """
    if not voivodeship_name:
        return POLAND_LOCATION_CODE
    normalized = voivodeship_name.strip().lower()
    return VOIVODESHIP_LOCATION_CODE_MAP.get(normalized, POLAND_LOCATION_CODE)


def is_blocked_for_scraping(url):
    """Zwraca True jesli URL nalezy do platformy ktorej nie mozna scrapowac."""
    if not url:
        return False
    return any(domain in url for domain in BLOCKED_SCRAPING_DOMAINS)
