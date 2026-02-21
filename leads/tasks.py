from celery import shared_task
from .models import Lead
from .services.email_scraper import scrape_email


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
