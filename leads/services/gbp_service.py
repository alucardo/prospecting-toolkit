"""
Google Business Profile OAuth2 + Performance API service.

Flow:
1. /google/oauth/start/       → redirect do Google z URL zgody
2. /google/oauth/callback/    → Google wraca z code, wymieniamy na refresh_token, zapisujemy
3. Potem używamy refresh_token do pobierania access_token i danych

Scope: https://www.googleapis.com/auth/business.manage
"""

import requests
from django.conf import settings


SCOPES = ['https://www.googleapis.com/auth/business.manage']

AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'
GBP_BASE = 'https://mybusinessbusinessinformation.googleapis.com/v1'
GBP_PERF_BASE = 'https://businessprofileperformance.googleapis.com/v1'


def get_authorization_url(redirect_uri):
    """Zwraca URL do przekierowania użytkownika na stronę zgody Google."""
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',   # żeby dostać refresh_token
        'prompt': 'consent',        # wymuś zgodę żeby zawsze dostać refresh_token
    }
    from urllib.parse import urlencode
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(code, redirect_uri):
    """Wymienia authorization code na access_token i refresh_token."""
    resp = requests.post(TOKEN_URL, data={
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    })
    resp.raise_for_status()
    return resp.json()  # zawiera access_token, refresh_token, expires_in


def get_access_token(refresh_token):
    """Używa refresh_token żeby dostać świeży access_token."""
    resp = requests.post(TOKEN_URL, data={
        'refresh_token': refresh_token,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'grant_type': 'refresh_token',
    })
    resp.raise_for_status()
    return resp.json()['access_token']


def _auth_headers(access_token):
    return {'Authorization': f'Bearer {access_token}'}


def list_locations(access_token):
    """Zwraca listę wszystkich lokalizacji z wszystkich kont.
    Używa wildcard '-' żeby ominąć Account Management API.
    """
    resp = requests.get(
        'https://mybusinessbusinessinformation.googleapis.com/v1/accounts/-/locations',
        headers=_auth_headers(access_token),
        params={
            'readMask': 'name,title,storefrontAddress,websiteUri',
            'pageSize': 100,
        },
    )
    resp.raise_for_status()
    return resp.json().get('locations', [])


def get_performance_metrics(access_token, location_name, date_from, date_to):
    """
    Pobiera metryki wydajności wizytówki.
    location_name format: 'locations/123456789'
    date_from / date_to: datetime.date
    """
    metrics = [
        'BUSINESS_IMPRESSIONS_DESKTOP_MAPS',
        'BUSINESS_IMPRESSIONS_MOBILE_MAPS',
        'BUSINESS_IMPRESSIONS_DESKTOP_SEARCH',
        'BUSINESS_IMPRESSIONS_MOBILE_SEARCH',
        'CALL_CLICKS',
        'DIRECTION_REQUESTS',
        'WEBSITE_CLICKS',
    ]

    payload = {
        'dailyRange': {
            'startDate': {
                'year': date_from.year,
                'month': date_from.month,
                'day': date_from.day,
            },
            'endDate': {
                'year': date_to.year,
                'month': date_to.month,
                'day': date_to.day,
            },
        },
        'metrics': [{'metric': m} for m in metrics],
    }

    resp = requests.post(
        f'{GBP_PERF_BASE}/{location_name}:fetchMultiDailyMetricsTimeSeries',
        headers={**_auth_headers(access_token), 'Content-Type': 'application/json'},
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


def parse_performance(raw):
    """
    Parsuje odpowiedź z fetchMultiDailyMetricsTimeSeries.
    Zwraca słownik: {metric_name: total, ...} + dane dzienne.
    """
    result = {}
    daily = {}

    for series in raw.get('multiDailyMetricTimeSeries', []):
        for item in series.get('dailyMetricTimeSeries', []):
            metric = item.get('dailyMetric')
            values = item.get('timeSeries', {}).get('datedValues', [])

            total = 0
            for dv in values:
                val = dv.get('value')
                if val is not None:
                    try:
                        total += int(val)
                    except (ValueError, TypeError):
                        pass

                # Dane dzienne — klucz: 'YYYY-MM-DD'
                date_obj = dv.get('date', {})
                if date_obj:
                    date_str = f"{date_obj.get('year', 0):04d}-{date_obj.get('month', 0):02d}-{date_obj.get('day', 0):02d}"
                    if date_str not in daily:
                        daily[date_str] = {}
                    daily[date_str][metric] = int(val or 0)

            result[metric] = total

    # Sumy zagregowane dla wygody
    result['impressions_maps'] = (
        result.get('BUSINESS_IMPRESSIONS_DESKTOP_MAPS', 0) +
        result.get('BUSINESS_IMPRESSIONS_MOBILE_MAPS', 0)
    )
    result['impressions_search'] = (
        result.get('BUSINESS_IMPRESSIONS_DESKTOP_SEARCH', 0) +
        result.get('BUSINESS_IMPRESSIONS_MOBILE_SEARCH', 0)
    )
    result['impressions_total'] = result['impressions_maps'] + result['impressions_search']
    result['daily'] = daily

    return result
