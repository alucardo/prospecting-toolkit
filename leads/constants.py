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


# Mapa polskich nazw województw na nazwy lokalizacji DataForSEO
# DataForSEO wymaga angielskich nazw regionów w formacie "X Voivodeship, Poland"
VOIVODESHIP_DATAFORSEO_MAP = {
    # Polskie nazwy (różne warianty) → DataForSEO location_name
    'dolnośląskie':             'Lower Silesian Voivodeship, Poland',
    'kujawsko-pomorskie':       'Kuyavian-Pomeranian Voivodeship, Poland',
    'lubelskie':                'Lublin Voivodeship, Poland',
    'lubuskie':                 'Lubusz Voivodeship, Poland',
    'łódzkie':                  'Lodz Voivodeship, Poland',
    'małopolskie':              'Lesser Poland Voivodeship, Poland',
    'mazowieckie':              'Masovian Voivodeship, Poland',
    'opolskie':                 'Opole Voivodeship, Poland',
    'podkarpackie':             'Subcarpathian Voivodeship, Poland',
    'podlaskie':                'Podlaskie Voivodeship, Poland',
    'pomorskie':                'Pomeranian Voivodeship, Poland',
    'śląskie':                  'Silesian Voivodeship, Poland',
    'świętokrzyskie':           'Holy Cross Voivodeship, Poland',
    'warmińsko-mazurskie':      'Warmian-Masurian Voivodeship, Poland',
    'wielkopolskie':            'Greater Poland Voivodeship, Poland',
    'zachodniopomorskie':       'West Pomeranian Voivodeship, Poland',
}


def get_dataforseo_location(voivodeship_name):
    """
    Zwraca nazwę lokalizacji DataForSEO na podstawie polskiej nazwy województwa.
    Porównuje bez względu na wielkość liter i białe znaki.
    Fallback: 'Poland' jeśli nie znaleziono.
    """
    if not voivodeship_name:
        return 'Poland'
    normalized = voivodeship_name.strip().lower()
    return VOIVODESHIP_DATAFORSEO_MAP.get(normalized, 'Poland')


def is_blocked_for_scraping(url):
    """Zwraca True jesli URL nalezy do platformy ktorej nie mozna scrapowac."""
    if not url:
        return False
    return any(domain in url for domain in BLOCKED_SCRAPING_DOMAINS)
