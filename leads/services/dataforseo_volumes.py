import requests
import base64


def fetch_keyword_volumes(phrases, login, password, location_code=2616, language_name="Polish"):
    """
    Pobiera miesięczne wolumeny wyszukiwań dla listy fraz z DataForSEO.
    Endpoint: keywords_data/google_ads/search_volume/live

    location_code: int — kod lokalizacji DataForSEO (nie string!)
        2616        = cała Polska (fallback)
        20847-20862 = poszczególne województwa
    Użyj get_dataforseo_location_code() z constants.py żeby pobrać kod dla województwa.

    Zwraca słownik: {fraza: volume_int_or_None}
    Przy błędzie zwraca pusty słownik.
    """
    if not phrases or not login or not password:
        return {}

    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }

    # google_ads/search_volume/live przyjmuje max 1000 fraz naraz
    CHUNK_SIZE = 1000
    result = {}

    for i in range(0, len(phrases), CHUNK_SIZE):
        chunk = phrases[i:i + CHUNK_SIZE]
        try:
            response = requests.post(
                "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
                headers=headers,
                json=[{
                    "keywords": chunk,
                    "location_code": location_code,
                    "language_name": language_name,
                }],
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()

            tasks = data.get("tasks") or []
            if not tasks:
                continue

            task = tasks[0]
            if task.get("status_code") != 20000:
                continue

            # google_ads/search_volume/live zwraca result jako plaska lista obiektow
            # (nie jest opakowana w dodatkowy slownik z kluczem 'items')
            items = task.get("result") or []
            for item in items:
                if not isinstance(item, dict):
                    continue
                keyword = item.get("keyword", "")
                volume = item.get("search_volume")
                if keyword:
                    result[keyword] = volume

        except Exception:
            continue

    return result
