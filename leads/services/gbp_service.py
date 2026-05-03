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
        'WEBSITE_CLICKS',
        'BUSINESS_CONVERSATIONS',
        'BUSINESS_BOOKINGS',
        'BUSINESS_FOOD_ORDERS',
        'BUSINESS_FOOD_MENU_CLICKS',
    ]

    from urllib.parse import urlencode
    date_params = [
        ('dailyRange.startDate.year', date_from.year),
        ('dailyRange.startDate.month', date_from.month),
        ('dailyRange.startDate.day', date_from.day),
        ('dailyRange.endDate.year', date_to.year),
        ('dailyRange.endDate.month', date_to.month),
        ('dailyRange.endDate.day', date_to.day),
    ]
    metric_params = [('dailyMetrics', m) for m in metrics]
    qs = urlencode(date_params + metric_params)

    resp = requests.get(
        f'{GBP_PERF_BASE}/{location_name}:fetchMultiDailyMetricsTimeSeries?{qs}',
        headers=_auth_headers(access_token),
    )
    if not resp.ok:
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')
    return resp.json()


def compute_monthly_snapshot(lead, year, month):
    """
    Sumuje dzienne wpisy API dla danego miesiąca i zapisuje/aktualizuje
    rekord miesięczny (day=None, source='api').
    Zwraca (snapshot, created) lub None jeśli brak danych dziennych.
    """
    from leads.models import GBPMetricsSnapshot
    from django.db.models import Sum

    daily = GBPMetricsSnapshot.objects.filter(
        lead=lead,
        year=year,
        month=month,
        day__isnull=False,
        source=GBPMetricsSnapshot.SOURCE_API,
    ).aggregate(
        calls=Sum('calls'),
        profile_views=Sum('profile_views'),
        website_visits=Sum('website_visits'),
        direction_requests=Sum('direction_requests'),
        conversations=Sum('conversations'),
        bookings=Sum('bookings'),
        food_orders=Sum('food_orders'),
        food_menu_clicks=Sum('food_menu_clicks'),
    )

    if all(v is None for v in daily.values()):
        return None

    snapshot, created = GBPMetricsSnapshot.objects.update_or_create(
        lead=lead,
        year=year,
        month=month,
        day=None,
        source=GBPMetricsSnapshot.SOURCE_API,
        defaults={
            'calls': daily['calls'] or 0,
            'profile_views': daily['profile_views'] or 0,
            'website_visits': daily['website_visits'] or 0,
            'direction_requests': daily['direction_requests'] or 0,
            'conversations': daily['conversations'] or 0,
            'bookings': daily['bookings'] or 0,
            'food_orders': daily['food_orders'] or 0,
            'food_menu_clicks': daily['food_menu_clicks'] or 0,
        },
    )
    return snapshot, created


def get_direction_requests(access_token, location_name, date_from, date_to):
    """
    Pobiera zapytania o trasę przez getDailyMetricsTimeSeries.
    Zwraca dict {date_str: count}.
    """
    from urllib.parse import urlencode
    params = [
        ('dailyMetric', 'BUSINESS_DIRECTION_REQUESTS'),
        ('dailyRange.startDate.year', date_from.year),
        ('dailyRange.startDate.month', date_from.month),
        ('dailyRange.startDate.day', date_from.day),
        ('dailyRange.endDate.year', date_to.year),
        ('dailyRange.endDate.month', date_to.month),
        ('dailyRange.endDate.day', date_to.day),
    ]
    qs = urlencode(params)
    resp = requests.get(
        f'{GBP_PERF_BASE}/{location_name}:getDailyMetricsTimeSeries?{qs}',
        headers=_auth_headers(access_token),
    )
    if not resp.ok:
        import logging
        logging.getLogger(__name__).warning(f'[GBP directions] HTTP {resp.status_code}: {resp.text[:200]}')
        return {}

    data = resp.json()
    result = {}

    # Spróbuj obu możliwych struktur odpowiedzi API
    # Struktura 1: {timeSeries: {datedValues: [{date: {}, value: N}]}}
    dated_values = data.get('timeSeries', {}).get('datedValues', [])

    # Struktura 2: {multiDailyMetricTimeSeries: [{dailyMetricTimeSeries: [{timeSeries: {datedValues: []}}]}]}
    if not dated_values:
        for series in data.get('multiDailyMetricTimeSeries', []):
            for item in series.get('dailyMetricTimeSeries', []):
                if item.get('dailyMetric') == 'DIRECTION_REQUESTS':
                    dated_values = item.get('timeSeries', {}).get('datedValues', [])
                    break

    for item in dated_values:
        d = item.get('date', {})
        if d:
            date_str = f"{d.get('year', 0)}-{d.get('month', 0):02d}-{d.get('day', 0):02d}"
            result[date_str] = int(item.get('value') or 0)

    import logging
    logging.getLogger(__name__).info(f'[GBP directions] pobrano {len(result)} dni')
    return result


def _metrics_to_snapshot_kwargs(metrics, direction_requests_map=None, date_str=None):
    """Przetwarza słownik metryk z API na kwargs do GBPMetricsSnapshot.objects.create()."""
    impressions = sum(
        metrics.get(m, 0) for m in [
            'BUSINESS_IMPRESSIONS_DESKTOP_MAPS',
            'BUSINESS_IMPRESSIONS_MOBILE_MAPS',
            'BUSINESS_IMPRESSIONS_DESKTOP_SEARCH',
            'BUSINESS_IMPRESSIONS_MOBILE_SEARCH',
        ]
    )
    return {
        'profile_views': impressions,
        'calls': metrics.get('CALL_CLICKS', 0),
        'website_visits': metrics.get('WEBSITE_CLICKS', 0),
        'direction_requests': direction_requests_map.get(date_str, 0) if direction_requests_map and date_str else None,
        'conversations': metrics.get('BUSINESS_CONVERSATIONS', 0),
        'bookings': metrics.get('BUSINESS_BOOKINGS', 0),
        'food_orders': metrics.get('BUSINESS_FOOD_ORDERS', 0),
        'food_menu_clicks': metrics.get('BUSINESS_FOOD_MENU_CLICKS', 0),
    }


def parse_performance(raw):
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
