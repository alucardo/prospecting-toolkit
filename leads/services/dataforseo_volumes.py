import requests
import base64


def fetch_keyword_volumes(phrases, login, password, location_name="Poland", language_name="Polish"):
    """
    Pobiera miesięczne wolumeny wyszukiwań dla listy fraz z DataForSEO.
    Endpoint: dataforseo_labs/google/bulk_keyword_metrics/live

    location_name powinno byc polem dataforseo_name z modelu Voivodeship,
    np. "Silesian Voivodeship, Poland" — nie ogolne "Poland".

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

    # DataForSEO przyjmuje max 1000 fraz naraz — dzielimy na chunki
    CHUNK_SIZE = 1000
    result = {}

    for i in range(0, len(phrases), CHUNK_SIZE):
        chunk = phrases[i:i + CHUNK_SIZE]
        try:
            response = requests.post(
                "https://api.dataforseo.com/v3/dataforseo_labs/google/bulk_keyword_metrics/live",
                headers=headers,
                json=[{
                    "keywords": chunk,
                    "location_name": location_name,
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

            task_result = (task.get("result") or [None])[0]
            if not task_result:
                continue

            items = task_result.get("items") or []
            for item in items:
                keyword = item.get("keyword", "")
                metrics = item.get("keyword_info") or {}
                volume = metrics.get("search_volume")
                # Normalizuj: None zostaje None, 0 zostaje 0
                result[keyword] = volume

        except Exception:
            continue

    return result
