"""
Serwis do publikowania postów na Google Business Profile.
Obsługuje tworzenie, usuwanie i pobieranie lokalnych postów (localPosts).
"""
import re
import requests

GBP_BASE = 'https://mybusiness.googleapis.com/v4'


def _auth_headers(access_token):
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }


def get_full_location_name(access_token, location_name_short):
    """
    Buduje pełną ścieżkę lokalizacji accounts/XXX/locations/YYY
    pobierając account ID z Account Management API.
    """
    loc_id = location_name_short.split('/')[-1]

    resp = requests.get(
        'https://mybusinessaccountmanagement.googleapis.com/v1/accounts',
        headers=_auth_headers(access_token),
        timeout=15,
    )
    if not resp.ok:
        raise ValueError(f'Nie można pobrać kont GBP: {resp.status_code} {resp.text[:200]}')

    accounts = resp.json().get('accounts', [])
    if not accounts:
        raise ValueError(f'Brak kont GBP. Odpowiedź: {resp.text[:300]}')

    # Użyj pierwszego konta — weryfikację pomijamy bo różne API mają różne zasady
    account_name = accounts[0].get('name', '')
    return f'{account_name}/locations/{loc_id}'


def _normalize_location_name_full(raw):
    """
    Zwraca pełną ścieżkę lokalizacji dla mybusiness.googleapis.com/v4.
    Format: accounts/XXX/locations/YYY
    """
    raw = raw.strip()
    if raw.startswith('accounts/'):
        return raw  # już pełna ścieżka
    elif raw.startswith('locations/'):
        return raw  # brak accountów — niektóre endpointy akceptują
    else:
        return 'locations/' + raw


def _normalize_location_name(raw):
    """
    Normalizuje location_name do formatu 'locations/XXXX'
    (używane przez Performance API).
    """
    raw = raw.strip()
    if '/locations/' in raw and raw.startswith('accounts/'):
        return 'locations/' + raw.split('/locations/')[-1]
    elif raw.startswith('locations/'):
        return raw
    else:
        return 'locations/' + raw


def _drive_url_to_media_url(drive_url):
    """
    Konwertuje link Google Drive na publiczny URL do pobrania pliku.
    Działa dla publicznie udostępnionych plików.
    """
    if not drive_url:
        return None
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        file_id = match.group(1)
        return f'https://drive.google.com/uc?export=download&id={file_id}'
    return None


# Mapowanie typów postów z naszego systemu na topicType GBP
POST_TYPE_MAP = {
    'news':    'STANDARD',
    'offer':   'OFFER',
    'event':   'EVENT',
}

# Mapowanie cta_type na actionType GBP
CTA_TYPE_MAP = {
    'LEARN_MORE': 'LEARN_MORE',
    'BOOK':       'BOOK',
    'ORDER':      'ORDER',
    'SHOP':       'SHOP',
    'SIGN_UP':    'SIGN_UP',
    'CALL':       'CALL',
}


def publish_local_post(access_token, location_name, body, topic_type='STANDARD',
                       cta_type=None, cta_url=None, drive_url=None,
                       title=None, event_start=None, event_end=None):
    """
    Publikuje post na wizytówce Google.

    Parametry:
        access_token  — aktualny token OAuth
        location_name — np. 'accounts/.../locations/...' lub 'locations/...'
        body          — treść posta (max 1500 znaków)
        topic_type    — 'STANDARD' | 'OFFER' | 'EVENT'
        cta_type      — opcjonalny typ przycisku (LEARN_MORE, BOOK, ORDER itd.)
        cta_url       — URL przycisku CTA
        drive_url     — link do zdjęcia na Google Drive (publiczny)
        title         — tytuł (wymagany dla OFFER i EVENT)
        event_start   — datetime ISO dla EVENT
        event_end     — datetime ISO dla EVENT

    Zwraca:
        dict z odpowiedzią API (zawiera 'name' posta = external_id)

    Rzuca:
        ValueError — jeśli API zwróci błąd
    """
    location = _normalize_location_name_full(location_name)
    url = f'{GBP_BASE}/{location}/localPosts'

    import logging
    logging.getLogger(__name__).info(f'[GBP publish] POST {url}')

    payload = {
        'languageCode': 'pl',
        'summary': body,
        'topicType': topic_type,
    }

    # Tytuł — tylko dla EVENT (wewnątrz pola event)
    # Dla STANDARD i OFFER nie ma pola title na poziomie posta

    # CTA
    if cta_type and cta_url:
        payload['callToAction'] = {
            'actionType': CTA_TYPE_MAP.get(cta_type, 'LEARN_MORE'),
            'url': cta_url,
        }
    elif cta_type == 'CALL' and cta_type:
        # CALL nie wymaga URL
        payload['callToAction'] = {
            'actionType': 'CALL',
        }

    # Zdjęcie
    media_url = _drive_url_to_media_url(drive_url)
    if media_url:
        payload['media'] = [{
            'mediaFormat': 'PHOTO',
            'sourceUrl': media_url,
        }]

    # Daty wydarzenia
    if topic_type == 'EVENT' and event_start and event_end:
        payload['event'] = {
            'title': title or body[:50],
            'schedule': {
                'startDate': _date_to_gbp(event_start),
                'startTime': _time_to_gbp(event_start),
                'endDate': _date_to_gbp(event_end),
                'endTime': _time_to_gbp(event_end),
            }
        }

    resp = requests.post(url, json=payload, headers=_auth_headers(access_token), timeout=30)

    if not resp.ok:
        try:
            error_msg = resp.json().get('error', {}).get('message', resp.text[:300])
        except Exception:
            error_msg = resp.text[:300]
        raise ValueError(f'GBP API error {resp.status_code} | URL: {url} | {error_msg}')

    return resp.json()


def delete_local_post(access_token, post_name):
    """
    Usuwa post z wizytówki Google.

    Parametry:
        access_token — aktualny token OAuth
        post_name    — pełna nazwa posta np. 'locations/XXX/localPosts/YYY'
    """
    url = f'{GBP_BASE}/{post_name}'
    resp = requests.delete(url, headers=_auth_headers(access_token), timeout=30)

    if not resp.ok:
        try:
            error_msg = resp.json().get('error', {}).get('message', resp.text[:300])
        except Exception:
            error_msg = resp.text[:300]
        raise ValueError(f'GBP API error {resp.status_code}: {error_msg}')

    return True


def list_local_posts(access_token, location_name, page_size=20):
    """
    Pobiera listę postów z wizytówki Google.

    Zwraca listę postów (dict) posortowaną od najnowszych.
    """
    location = _normalize_location_name(location_name)
    url = f'{GBP_BASE}/{location}/localPosts'
    params = {'pageSize': page_size}

    resp = requests.get(url, params=params, headers=_auth_headers(access_token), timeout=30)

    if not resp.ok:
        try:
            error_msg = resp.json().get('error', {}).get('message', resp.text[:300])
        except Exception:
            error_msg = resp.text[:300]
        raise ValueError(f'GBP API error {resp.status_code}: {error_msg}')

    return resp.json().get('localPosts', [])


# ── Helpery dat ──────────────────────────────────────────────────────────────

def _date_to_gbp(dt):
    """Konwertuje datetime na format daty GBP {year, month, day}."""
    return {'year': dt.year, 'month': dt.month, 'day': dt.day}


def _time_to_gbp(dt):
    """Konwertuje datetime na format czasu GBP {hours, minutes}."""
    return {'hours': dt.hour, 'minutes': dt.minute}
