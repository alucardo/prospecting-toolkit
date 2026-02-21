from apify_client import ApifyClient
from django.conf import settings
import requests
from django.conf import settings

def get_account_info():
    response = requests.get(
        'https://api.apify.com/v2/users/me/usage/monthly',
        headers={'Authorization': f'Bearer {settings.APIFY_API_TOKEN}'}
    )
    return response.json()

def get_apify_balance():
    import requests
    from django.core.cache import cache

    cached = cache.get('apify_balance')
    if cached:
        return cached

    headers = {'Authorization': f'Bearer {settings.APIFY_API_TOKEN}'}

    usage_response = requests.get(
        'https://api.apify.com/v2/users/me/usage/monthly',
        headers=headers
    )
    user_response = requests.get(
        'https://api.apify.com/v2/users/me',
        headers=headers
    )

    usage_data = usage_response.json().get('data', {})
    user_data = user_response.json().get('data', {})

    monthly_limit = user_data.get('plan', {}).get('monthlyUsageCreditsUsd', 5.00)
    spent = usage_data.get('totalUsageCreditsUsdAfterVolumeDiscount', 0)
    remaining = monthly_limit - spent

    result = {
        'spent': round(spent, 4),
        'remaining': round(remaining, 4),
        'limit': monthly_limit,
        'cycle_start': usage_data.get('usageCycle', {}).get('startAt', ''),
        'cycle_end': usage_data.get('usageCycle', {}).get('endAt', ''),
    }

    cache.set('apify_balance', result, timeout=1500)  # cache na 25 minut

    return result

def run_google_maps_scraper(keyword, city, limit):
    client = ApifyClient(settings.APIFY_API_TOKEN)

    run_input = {
        "searchStringsArray": [keyword],
        "locationQuery": city,
        "countryCode": "pl",
        "language": "pl",
        "maxCrawledPlacesPerSearch": limit,
        "includeWebResults": False,
        "scrapeDirectories": False,
        "scrapePlaceDetailPage": False,
        "scrapeTableReservationProvider": False,
        "skipClosedPlaces": False,
    }

    run = client.actor("compass/google-maps-extractor").call(run_input=run_input)

    return run.get("id"), run.get("status")


def fetch_results(run_id):
    client = ApifyClient(settings.APIFY_API_TOKEN)

    run = client.run(run_id).get()
    dataset_id = run["defaultDatasetId"]

    items = []
    for item in client.dataset(dataset_id).iterate_items():
        items.append(item)

    return items

def normalize_address(address):
    if not address:
        return ''
    return address.split(',')[0].strip().lower()


def fetch_and_save_leads(search_query):
    from leads.models import Lead

    client = ApifyClient(settings.APIFY_API_TOKEN)

    run = client.run(search_query.apify_run_id).get()
    dataset_id = run["defaultDatasetId"]

    leads_created = 0
    leads_skipped = 0

    for item in client.dataset(dataset_id).iterate_items():
        name = item.get('title', '').strip()
        address = item.get('address', '')

        existing = Lead.objects.filter(
            name__iexact=name,
            city=search_query.city
        )
        if existing.exists():
            if any(normalize_address(l.address) == normalize_address(address) for l in existing):
                leads_skipped += 1
                continue

        Lead.objects.create(
            city=search_query.city,
            source='google_maps',
            name=name,
            phone=item.get('phone', ''),
            address=address,
            email=item.get('email', ''),
            website=item.get('website', ''),
            raw_data=item,
        )
        leads_created += 1

    return leads_created, leads_skipped