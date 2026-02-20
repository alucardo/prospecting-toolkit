from apify_client import ApifyClient
from django.conf import settings


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

def fetch_and_save_leads(search_query):
    from leads.models import Lead

    client = ApifyClient(settings.APIFY_API_TOKEN)

    run = client.run(search_query.apify_run_id).get()
    dataset_id = run["defaultDatasetId"]

    leads_created = 0
    for item in client.dataset(dataset_id).iterate_items():
        Lead.objects.create(
            city=search_query.city,
            source='google_maps',
            name=item.get('title', ''),
            phone=item.get('phone', ''),
            address=item.get('address', ''),
            email=item.get('email', ''),
            website=item.get('website', ''),
            raw_data=item,
        )
        leads_created += 1

    return leads_created