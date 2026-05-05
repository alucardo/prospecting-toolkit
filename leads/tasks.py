import os
import tempfile
import base64
import logging
from celery import shared_task
from .models import Lead, SearchQuery, UserContact, Voivodeship, VoivodeshipKeyword
from .services.email_scraper import scrape_email
from .services.apify import fetch_and_save_leads
from .services.pdf_service import html_to_pdf

logger = logging.getLogger(__name__)


@shared_task
def fetch_gbp_metrics_all():
    """
    Nocny task — pobiera dane GBP dla wszystkich klientów
    i aktualizuje sumy miesięczne.
    """
    from datetime import date, timedelta
    from django.utils import timezone
    from django.db.models import Sum
    from .models import GBPMetricsSnapshot, AppSettings
    from .services.gbp_service import (
    get_access_token, get_performance_metrics,
    parse_performance, compute_monthly_snapshot,
    _metrics_to_snapshot_kwargs, get_direction_requests,
    )

    settings = AppSettings.get()
    if not settings.google_refresh_token:
        logger.warning('[GBP metrics] Brak Google Refresh Token — pomijam')
        return

    try:
        access_token = get_access_token(settings.google_refresh_token)
    except Exception as e:
        logger.error(f'[GBP metrics] Błąd access token: {e}')
        return

    # Klienci z przypisanym GBP location
    clients = Lead.objects.filter(
        status='client',
        gbp_location_name__isnull=False,
    ).exclude(gbp_location_name='')

    today = timezone.now().date()
    date_to = today - timedelta(days=5)   # bufor na opóźnienie Google
    date_from = today - timedelta(days=35)

    logger.info(f'[GBP metrics] Start dla {clients.count()} klientów, zakres {date_from}–{date_to}')

    for lead in clients:
        try:
            # Normalizacja location_name
            stored = lead.gbp_location_name.strip()
            if '/locations/' in stored and stored.startswith('accounts/'):
                location_name = 'locations/' + stored.split('/locations/')[-1]
            elif stored.startswith('locations/'):
                location_name = stored
            else:
                location_name = 'locations/' + stored

            # Sprawdź jakich dni brakuje
            existing_days = set(
                GBPMetricsSnapshot.objects
                .filter(
                    lead=lead,
                    source=GBPMetricsSnapshot.SOURCE_API,
                    day__isnull=False,
                    year__gte=date_from.year,
                )
                .values_list('year', 'month', 'day')
            )

            all_days = set()
            d = date_from
            while d <= date_to:
                all_days.add((d.year, d.month, d.day))
                d += timedelta(days=1)

            missing = all_days - existing_days
            if not missing:
                logger.info(f'[GBP metrics] {lead.name} — wszystkie dni są w bazie, pomijam API')
            else:
                raw = get_performance_metrics(access_token, location_name, date_from, date_to)
                parsed = parse_performance(raw)
                daily_data = parsed.get('daily', {})
                direction_map = get_direction_requests(access_token, location_name, date_from, date_to)

                saved = 0
                for date_str, metrics in daily_data.items():
                    try:
                        d = date.fromisoformat(date_str)
                    except ValueError:
                        continue

                    if (d.year, d.month, d.day) in existing_days:
                        continue

                    GBPMetricsSnapshot.objects.create(
                        lead=lead,
                        year=d.year, month=d.month, day=d.day,
                        source=GBPMetricsSnapshot.SOURCE_API,
                        **_metrics_to_snapshot_kwargs(metrics, direction_map, date_str),
                    )
                    saved += 1

                logger.info(f'[GBP metrics] {lead.name} — zapisano {saved} nowych dni')

            # Aktualizuj sumy miesięczne dla miesięcy w zakresie
            months_in_range = set()
            d = date_from
            while d <= date_to:
                months_in_range.add((d.year, d.month))
                d += timedelta(days=1)

            for year, month in months_in_range:
                try:
                    result = compute_monthly_snapshot(lead, year, month)
                    if result:
                        snap, created = result
                        action = 'utworzono' if created else 'zaktualizowano'
                        logger.info(f'[GBP metrics] {lead.name} — {action} sumę {month:02d}/{year}')
                except Exception as month_err:
                    logger.warning(f'[GBP metrics] {lead.name} — błąd sumy {month:02d}/{year}: {month_err}')

        except Exception as e:
            logger.error(f'[GBP metrics] Błąd dla {lead.name}: {e}')
            continue

    logger.info('[GBP metrics] Zakończono')


@shared_task
def check_unread_emails_task():
    """Co godzinę sprawdza nieprzeczytane emaile i ustawia flagę."""
    from django.utils import timezone
    from .models import AppSettings
    from .services.imap_service import get_unread_emails

    settings = AppSettings.get()
    if not settings.imap_host or not settings.imap_username or not settings.imap_password:
        logger.info('[email check] Brak konfiguracji IMAP — pomijam')
        return

    try:
        emails = get_unread_emails(settings)
        settings.has_unread_emails = len(emails) > 0
        settings.unread_emails_checked_at = timezone.now()
        settings.save(update_fields=['has_unread_emails', 'unread_emails_checked_at'])
        logger.info(f'[email check] Nieprzeczytane: {len(emails)}')
    except Exception as e:
        logger.error(f'[email check] Błąd: {e}')


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
    import logging
    from django.utils import timezone
    from .models import AppSettings
    from .services.dataforseo_volumes import fetch_keyword_volumes
    from .constants import get_dataforseo_location_code

    logger = logging.getLogger(__name__)

    voivodeship = Voivodeship.objects.get(pk=voivodeship_id)
    app_settings = AppSettings.get()
    logger.info(f'[keyword volumes] start dla {voivodeship.name}, login={repr(app_settings.dataforseo_login)}')

    if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
        logger.warning('[keyword volumes] brak credentials DataForSEO')
        return

    # Reset daty dla fraz ktore byly sprawdzane z blednym endpointem
    reset_count = voivodeship.keywords.filter(
        monthly_searches__isnull=True,
        searches_updated_at__isnull=False,
    ).update(searches_updated_at=None)
    logger.info(f'[keyword volumes] reset searches_updated_at dla {reset_count} fraz')

    keywords_to_update = list(
        voivodeship.keywords.filter(monthly_searches__isnull=True)
    )
    logger.info(f'[keyword volumes] fraz do pobrania: {len(keywords_to_update)}')
    if not keywords_to_update:
        logger.warning('[keyword volumes] brak fraz do pobrania')
        return

    # Oczyszczamy frazy — DataForSEO odrzuca caly batch jesli jedna fraza ma niedozwolone znaki
    import re as _re
    def clean_phrase(p):
        p = p.strip()
        p = p.strip('.,;:!?()[]{}\"\'')
        p = _re.sub(r'[^\w\s\-]', '', p, flags=_re.UNICODE)
        p = p.strip()
        return p

    # Mapowanie: oczyszczona fraza -> obiekt keyword (do pozniejszego zapisu)
    phrase_to_kw = {}
    for kw in keywords_to_update:
        cleaned = clean_phrase(kw.phrase)
        if cleaned:
            phrase_to_kw[cleaned] = kw

    phrases = list(phrase_to_kw.keys())
    logger.info(f'[keyword volumes] przyklad fraz po czyszczeniu: {phrases[:5]}')
    location_code = get_dataforseo_location_code(voivodeship.name)
    logger.info(f'[keyword volumes] odpytuje DataForSEO: {len(phrases)} fraz, location_code={location_code}')

    # Wywolanie API bezposrednio (bez serwisu) zeby uniknac problemow z cache .pyc
    import requests as req
    import base64 as b64
    credentials = b64.b64encode(
        f"{app_settings.dataforseo_login}:{app_settings.dataforseo_password}".encode()
    ).decode()
    headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/json"}

    volumes = {}
    CHUNK = 1000
    for i in range(0, len(phrases), CHUNK):
        chunk = phrases[i:i + CHUNK]
        try:
            resp = req.post(
                "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
                headers=headers,
                json=[{"keywords": chunk, "location_code": location_code, "language_name": "Polish"}],
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            task0 = (data.get('tasks') or [{}])[0]
            logger.info(f'[keyword volumes] chunk {i}: status={task0.get("status_code")}, msg={task0.get("status_message")}, result_count={task0.get("result_count")}, sent_data={task0.get("data")}')
            for item in (task0.get('result') or []):
                if isinstance(item, dict) and item.get('keyword'):
                    volumes[item['keyword']] = item.get('search_volume')
        except Exception as e:
            logger.error(f'[keyword volumes] blad chunk {i}: {e}')

    logger.info(f'[keyword volumes] DataForSEO zwrocil {len(volumes)} wynikow')

    now = timezone.now()
    updated = 0
    for cleaned_phrase, kw in phrase_to_kw.items():
        volume = volumes.get(cleaned_phrase)
        if volume is not None:
            kw.monthly_searches = str(volume)
            kw.searches_updated_at = now
            kw.save(update_fields=['monthly_searches', 'searches_updated_at'])
            updated += 1
        else:
            kw.searches_updated_at = now
            kw.save(update_fields=['searches_updated_at'])

    logger.info(f'[keyword volumes] zapisano {updated} wolumenow dla {voivodeship.name}')


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
