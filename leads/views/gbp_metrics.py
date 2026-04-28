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
        try:
            from ..services.gbp_service import get_access_token, get_performance_metrics, parse_performance
            yesterday = (timezone.now() - timedelta(days=1)).date()

            settings = AppSettings.get()
            access_token = get_access_token(settings.google_refresh_token)

            # Normalizuj location_name — jeśli zawiera ścieżkę accounts/.../locations/... to wytnij samo locations/...
            location_name = lead.gbp_location_name.strip()
            if '/locations/' in location_name and location_name.startswith('accounts/'):
                location_name = 'locations/' + location_name.split('/locations/')[-1]

            raw_result = get_performance_metrics(
                access_token,
                location_name,
                yesterday,
                yesterday,
            )
            parsed = parse_performance(raw_result)
        except Exception as e:
            import traceback
            error = f'{e}'
            error_trace = traceback.format_exc()
    else:
        error_trace = None
        location_name = lead.gbp_location_name

    return render(request, 'leads/gbp_metrics/fetch_test.html', {
        'lead': lead,
        'error': error,
        'error_trace': error_trace if 'error_trace' in dir() else None,
        'raw_result': json.dumps(raw_result, indent=2, ensure_ascii=False) if raw_result else None,
        'parsed': parsed,
        'yesterday': (timezone.now() - timedelta(days=1)).date(),
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
