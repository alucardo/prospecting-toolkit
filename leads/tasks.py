from celery import shared_task
from .models import Lead, SearchQuery
from .services.email_scraper import scrape_email
from .services.apify import fetch_and_save_leads


@shared_task
def scrape_lead_email(lead_id):
    lead = Lead.objects.get(pk=lead_id)
    email, source = scrape_email(lead.website)
    if email:
        lead.email = email
    lead.email_scraped = True
    lead.save()


@shared_task
def scrape_leads_emails_bulk(lead_ids):
    for lead_id in lead_ids:
        scrape_lead_email.delay(lead_id)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def fetch_apify_results(self, search_query_id):
    try:
        sq = SearchQuery.objects.get(pk=search_query_id)
        sq.status = 'fetching'
        sq.save(update_fields=['status'])

        leads_created, leads_skipped = fetch_and_save_leads(sq)

        sq.status = 'SUCCEEDED'
        sq.save(update_fields=['status'])
    except Exception as exc:
        try:
            sq = SearchQuery.objects.get(pk=search_query_id)
            sq.status = 'FAILED'
            sq.save(update_fields=['status'])
        except Exception:
            pass
        raise self.retry(exc=exc)
