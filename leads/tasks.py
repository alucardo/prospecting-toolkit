import os
import tempfile
import base64
from celery import shared_task
from .models import Lead, SearchQuery, UserContact, Voivodeship, VoivodeshipKeyword
from .services.email_scraper import scrape_email
from .services.apify import fetch_and_save_leads
from .services.pdf_service import html_to_pdf


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


@shared_task(bind=True, time_limit=300)
def generate_pdf_report(self, lead_pk, user_pk):
    """
    Generuje PDF raportu w tle i zapisuje do pliku tymczasowego.
    Zwraca ścieżkę do pliku — polling endpoint serwuje go i usuwa.
    """
    from django.template.loader import render_to_string
    from .views.reports import _get_context_for_task

    context = _get_context_for_task(lead_pk, user_pk)
    html = render_to_string('leads/reports/google_analysis.html', context)
    pdf_bytes = html_to_pdf(html)

    # Zapisz do pliku tymczasowego z unikalną nazwą (task_id)
    tmp_dir = tempfile.gettempdir()
    out_path = os.path.join(tmp_dir, f'pdf_report_{self.request.id}.pdf')
    with open(out_path, 'wb') as f:
        f.write(pdf_bytes)

    return out_path


@shared_task(bind=True, time_limit=300)
def fetch_keyword_volumes_task(self, voivodeship_id):
    """Pobiera wolumeny wyszukan z DataForSEO dla fraz bez wartosci w tle."""
    from django.utils import timezone
    from django.db import models as db_models
    from .models import AppSettings
    from .services.dataforseo_volumes import fetch_keyword_volumes
    from .constants import get_dataforseo_location_code

    voivodeship = Voivodeship.objects.get(pk=voivodeship_id)
    app_settings = AppSettings.get()

    if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
        return

    # Reset daty dla fraz ktore byly sprawdzane z blednym endpointem
    voivodeship.keywords.filter(
        monthly_searches__isnull=True,
        searches_updated_at__isnull=False,
    ).update(searches_updated_at=None)

    keywords_to_update = list(
        voivodeship.keywords.filter(monthly_searches__isnull=True)
    )
    if not keywords_to_update:
        return

    phrases = [kw.phrase for kw in keywords_to_update]
    location_code = get_dataforseo_location_code(voivodeship.name)
    volumes = fetch_keyword_volumes(
        phrases,
        app_settings.dataforseo_login,
        app_settings.dataforseo_password,
        location_code=location_code,
    )

    now = timezone.now()
    for kw in keywords_to_update:
        volume = volumes.get(kw.phrase)
        if volume is not None:
            kw.monthly_searches = str(volume)
            kw.searches_updated_at = now
            kw.save(update_fields=['monthly_searches', 'searches_updated_at'])
        else:
            kw.searches_updated_at = now
            kw.save(update_fields=['searches_updated_at'])


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_apify_results(self, search_query_id):
    import time
    from apify_client import ApifyClient
    from django.conf import settings

    try:
        sq = SearchQuery.objects.get(pk=search_query_id)

        # Czekaj az Apify skonczy (max 10 min)
        client = ApifyClient(settings.APIFY_API_TOKEN)
        for _ in range(60):
            run = client.run(sq.apify_run_id).get()
            status = run.get('status')
            if status == 'SUCCEEDED':
                break
            elif status in ('FAILED', 'ABORTED', 'TIMED-OUT'):
                sq.status = 'FAILED'
                sq.save(update_fields=['status'])
                return
            time.sleep(10)
        else:
            sq.status = 'FAILED'
            sq.save(update_fields=['status'])
            return

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
