import calendar
import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Lead, GBPMetricsSnapshot, AppSettings


@login_required
def gbp_metrics_fetch_test(request, lead_pk):
    """Krok 1: pobiera dane za wczoraj z API i pokazuje surowy wynik."""
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    error = None
    raw_result = None
    parsed = None

    # Sprawdź warunki wstępne
    if not lead.gbp_location_name:
        error = 'Brak GBP Location Name dla tego klienta. Uzupełnij pole w edycji leada.'
    else:
        settings = AppSettings.get()
        if not settings.google_refresh_token:
            error = 'Brak Google Refresh Token. Autoryzuj konto Google w Ustawieniach.'

    if not error and request.method == 'POST':
        action = request.POST.get('action', 'fetch')
        test_date = (timezone.now() - timedelta(days=7)).date()

        # Normalizacja location_name
        stored = lead.gbp_location_name.strip()
        if '/locations/' in stored and stored.startswith('accounts/'):
            location_name = 'locations/' + stored.split('/locations/')[-1]
        elif stored.startswith('locations/'):
            location_name = stored
        else:
            location_name = 'locations/' + stored

        if action == 'fetch_30':
            # Pobierz ostatnie 30 dni z wyłączeniem okresu bez danych (ostatnie 5 dni)
            date_to = (timezone.now() - timedelta(days=5)).date()
            date_from = date_to - timedelta(days=29)

            # Znajdź dni które już są w bazie
            existing_days = set(
                GBPMetricsSnapshot.objects
                .filter(
                    lead=lead,
                    source=GBPMetricsSnapshot.SOURCE_API,
                    day__isnull=False,
                    year__gte=date_from.year,
                )
                .filter(
                    day__isnull=False,
                )
                .values_list('year', 'month', 'day')
            )

            # Wszystkie dni w zakresie
            all_days = set()
            d = date_from
            while d <= date_to:
                all_days.add((d.year, d.month, d.day))
                d += timedelta(days=1)

            missing_days = all_days - existing_days

            if not missing_days:
                saved = True
                already_existed = True
                parsed = None
                raw_result = None
                saved_count = 0
                skipped_count = len(all_days)
                error_trace = None
            else:
                try:
                    from ..services.gbp_service import get_access_token, get_performance_metrics, parse_performance
                    settings = AppSettings.get()
                    access_token = get_access_token(settings.google_refresh_token)

                    raw_result = get_performance_metrics(
                        access_token,
                        location_name,
                        date_from,
                        date_to,
                    )
                    parsed_full = parse_performance(raw_result)
                    daily_data = parsed_full.get('daily', {})

                    saved_count = 0
                    skipped_count = len(existing_days)

                    for date_str, metrics in daily_data.items():
                        try:
                            from datetime import date as date_cls
                            d = date_cls.fromisoformat(date_str)
                        except ValueError:
                            continue

                        key = (d.year, d.month, d.day)
                        if key in existing_days:
                            continue  # pomijamy — jest już w bazie

                        impressions = sum(
                            metrics.get(m, 0) for m in [
                                'BUSINESS_IMPRESSIONS_DESKTOP_MAPS',
                                'BUSINESS_IMPRESSIONS_MOBILE_MAPS',
                                'BUSINESS_IMPRESSIONS_DESKTOP_SEARCH',
                                'BUSINESS_IMPRESSIONS_MOBILE_SEARCH',
                            ]
                        )
                        GBPMetricsSnapshot.objects.create(
                            lead=lead,
                            year=d.year,
                            month=d.month,
                            day=d.day,
                            source=GBPMetricsSnapshot.SOURCE_API,
                            profile_views=impressions,
                            calls=metrics.get('CALL_CLICKS', 0),
                            website_visits=metrics.get('WEBSITE_CLICKS', 0),
                            direction_requests=None,
                        )
                        saved_count += 1

                    saved = True
                    already_existed = False
                    parsed = None
                    error_trace = None

                except Exception as e:
                    import traceback
                    import requests as req_lib
                    if isinstance(e, req_lib.HTTPError) and e.response is not None:
                        error = f'HTTP {e.response.status_code}: {e.response.text[:500]}'
                    else:
                        error = str(e)
                    error_trace = traceback.format_exc()
                    saved = False
                    already_existed = False
                    saved_count = 0
                    skipped_count = 0

        else:
            saved_count = None
            skipped_count = None

            # Sprawdź czy wpis już jest w bazie — jeśli tak, nie odpytuj API
            existing = GBPMetricsSnapshot.objects.filter(
                lead=lead,
                year=test_date.year,
                month=test_date.month,
                day=test_date.day,
                source=GBPMetricsSnapshot.SOURCE_API,
            ).first()

            if existing:
                parsed = {
                    'CALL_CLICKS': existing.calls or 0,
                    'impressions_total': existing.profile_views or 0,
                    'impressions_maps': 0,
                    'impressions_search': 0,
                    'WEBSITE_CLICKS': existing.website_visits or 0,
                }
                raw_result = None
                saved = True
                already_existed = True
                error_trace = None
            else:
                try:
                    from ..services.gbp_service import get_access_token, get_performance_metrics, parse_performance

                    settings = AppSettings.get()
                    access_token = get_access_token(settings.google_refresh_token)

                    raw_result = get_performance_metrics(
                        access_token,
                        location_name,
                        test_date,
                        test_date,
                    )
                    parsed = parse_performance(raw_result)

                    if action == 'save' and parsed:
                        profile_views = parsed.get('impressions_total', 0)
                        calls = parsed.get('CALL_CLICKS', 0)
                        website_visits = parsed.get('WEBSITE_CLICKS', 0)

                        GBPMetricsSnapshot.objects.create(
                            lead=lead,
                            year=test_date.year,
                            month=test_date.month,
                            day=test_date.day,
                            source=GBPMetricsSnapshot.SOURCE_API,
                            profile_views=profile_views,
                            calls=calls,
                            website_visits=website_visits,
                            direction_requests=None,
                        )
                        saved = True
                        already_existed = False
                    else:
                        saved = False
                        already_existed = False

                except Exception as e:
                    import traceback
                    import requests as req_lib
                    if isinstance(e, req_lib.HTTPError) and e.response is not None:
                        error = f'HTTP {e.response.status_code}: {e.response.text[:500]}'
                    else:
                        error = str(e)
                    error_trace = traceback.format_exc()
                    saved = False
                    already_existed = False

    return render(request, 'leads/gbp_metrics/fetch_test.html', {
        'lead': lead,
        'error': error,
        'error_trace': error_trace if 'error_trace' in dir() else None,
        'raw_result': json.dumps(raw_result, indent=2, ensure_ascii=False) if raw_result else None,
        'parsed': parsed,
        'saved': saved,
        'already_existed': already_existed if 'already_existed' in dir() else False,
        'saved_count': saved_count if 'saved_count' in dir() else None,
        'skipped_count': skipped_count if 'skipped_count' in dir() else None,
        'test_date': (timezone.now() - timedelta(days=7)).date(),
        'location_name_used': location_name if 'location_name' in dir() else lead.gbp_location_name,
        'api_url_preview': f'https://businessprofileperformance.googleapis.com/v1/{location_name}:fetchMultiDailyMetricsTimeSeries' if 'location_name' in dir() else None,
    })


@login_required
def gbp_metrics_index(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    now = timezone.now()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            year = int(request.POST.get('year', now.year))
            month = int(request.POST.get('month', now.month))
            calls = request.POST.get('calls') or None
            profile_views = request.POST.get('profile_views') or None
            direction_requests = request.POST.get('direction_requests') or None
            website_visits = request.POST.get('website_visits') or None

            GBPMetricsSnapshot.objects.update_or_create(
                lead=lead,
                year=year,
                month=month,
                day=None,
                source=GBPMetricsSnapshot.SOURCE_MANUAL,
                defaults={
                    'calls': calls,
                    'profile_views': profile_views,
                    'direction_requests': direction_requests,
                    'website_visits': website_visits,
                },
            )

        elif action == 'delete':
            pk = request.POST.get('pk')
            GBPMetricsSnapshot.objects.filter(pk=pk, lead=lead).delete()

        return redirect('leads:gbp_metrics_index', lead_pk=lead.pk)

    # Tylko ręczne wpisy miesięczne (day=NULL) — dzienne pojawią się z API
    snapshots = lead.gbp_metrics.filter(day__isnull=True, source=GBPMetricsSnapshot.SOURCE_MANUAL)

    # Miesiące do selecta — bieżący rok i rok poprzedni
    months = [(y, m) for y in [now.year, now.year - 1] for m in range(1, 13)]
    months_choices = [
        (y, m, f"{calendar.month_name[m]} {y}")
        for y, m in months
    ]

    return render(request, 'leads/gbp_metrics/index.html', {
        'lead': lead,
        'snapshots': snapshots,
        'months_choices': months_choices,
        'current_year': now.year,
        'current_month': now.month,
    })
