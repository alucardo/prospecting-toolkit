import calendar
import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Lead, GBPMetricsSnapshot, AppSettings


@login_required
def gbp_metrics_fetch_test(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    error = None
    raw_result = None
    parsed = None
    saved = False
    already_existed = False
    saved_count = None
    skipped_count = None
    error_trace = None
    location_name = lead.gbp_location_name
    now = timezone.now()

    # Domyślne wartości formularza
    default_year = now.year
    default_month = now.month - 1 if now.month > 1 else 12
    if default_month == 12:
        default_year -= 1

    # Opcje miesięcy do selecta
    MONTHS_PL = ['', 'Styczeń', 'Luty', 'Marzec', 'Kwiecień', 'Maj', 'Czerwiec',
                 'Lipiec', 'Sierpień', 'Wrzesień', 'Październik', 'Listopad', 'Grudzień']
    month_choices = [
        (y, m, f"{MONTHS_PL[m]} {y}")
        for y in [now.year, now.year - 1]
        for m in range(1, 13)
    ]

    if not lead.gbp_location_name:
        error = 'Brak GBP Location Name dla tego klienta. Uzupełnij pole w edycji leada.'
    else:
        settings = AppSettings.get()
        if not settings.google_refresh_token:
            error = 'Brak Google Refresh Token. Autoryzuj konto Google w Ustawieniach.'

    if not error and request.method == 'POST':
        action = request.POST.get('action', 'fetch_30')

        # Normalizacja location_name
        stored = lead.gbp_location_name.strip()
        if '/locations/' in stored and stored.startswith('accounts/'):
            location_name = 'locations/' + stored.split('/locations/')[-1]
        elif stored.startswith('locations/'):
            location_name = stored
        else:
            location_name = 'locations/' + stored

        # Wyznacz zakres dat
        from datetime import date as date_cls
        import calendar as cal_mod

        if action == 'fetch_30':
            date_to = (now - timedelta(days=5)).date()
            date_from = date_to - timedelta(days=29)
        elif action == 'fetch_month':
            year = int(request.POST.get('month_year', default_year))
            month = int(request.POST.get('month_month', default_month))
            date_from = date_cls(year, month, 1)
            last_day = cal_mod.monthrange(year, month)[1]
            date_to = min(date_cls(year, month, last_day), (now - timedelta(days=5)).date())
        else:
            date_from = date_to = (now - timedelta(days=7)).date()

        # Znajdź dni które już są w bazie
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

        missing_days = all_days - existing_days

        force_refresh = request.POST.get('force_refresh') == '1'
        if force_refresh:
            # Usuń istniejące wpisy z tego zakresu przed ponownym pobraniem
            GBPMetricsSnapshot.objects.filter(
                lead=lead,
                source=GBPMetricsSnapshot.SOURCE_API,
                day__isnull=False,
                year__gte=date_from.year,
            ).filter(
                year__lte=date_to.year,
            ).exclude(
                year=date_from.year, month__lt=date_from.month,
            ).exclude(
                year=date_to.year, month__gt=date_to.month,
            ).delete()
            existing_days = set()
            missing_days = all_days

        if not missing_days:
            saved = True
            already_existed = True
            saved_count = 0
            skipped_count = len(all_days)
            error_trace = None
        else:
            try:
                from ..services.gbp_service import get_access_token, get_performance_metrics, parse_performance, compute_monthly_snapshot, _metrics_to_snapshot_kwargs, get_direction_requests
                settings = AppSettings.get()
                access_token = get_access_token(settings.google_refresh_token)

                raw_result = get_performance_metrics(access_token, location_name, date_from, date_to)
                parsed_full = parse_performance(raw_result)
                daily_data = parsed_full.get('daily', {})

                # Pobierz trasy osobnym endpointem
                direction_map = get_direction_requests(access_token, location_name, date_from, date_to)
                # Loguj dla debugowania
                import logging
                logging.getLogger(__name__).info(f'[GBP test] direction_map sample: {dict(list(direction_map.items())[:3])}')

                saved_count = 0
                skipped_count = len(existing_days)

                for date_str, metrics in daily_data.items():
                    try:
                        d = date_cls.fromisoformat(date_str)
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
                    saved_count += 1

                # Aktualizuj sumy miesięczne
                months_in_range = set()
                d = date_from
                while d <= date_to:
                    months_in_range.add((d.year, d.month))
                    d += timedelta(days=1)
                for year, month in months_in_range:
                    compute_monthly_snapshot(lead, year, month)

                saved = True
                already_existed = False
                error_trace = None

            except Exception as e:
                import traceback
                error = str(e)
                error_trace = traceback.format_exc()
                saved = False
                saved_count = 0
                skipped_count = 0

    return render(request, 'leads/gbp_metrics/fetch_test.html', {
        'lead': lead,
        'error': error,
        'error_trace': error_trace,
        'raw_result': json.dumps(raw_result, indent=2, ensure_ascii=False) if raw_result else None,
        'parsed': parsed,
        'saved': saved,
        'already_existed': already_existed,
        'saved_count': saved_count,
        'skipped_count': skipped_count,
        'location_name_used': location_name,
        'month_choices': month_choices,
        'default_year': default_year,
        'default_month': default_month,
        'api_url_preview': f'https://businessprofileperformance.googleapis.com/v1/{location_name}:fetchMultiDailyMetricsTimeSeries',
    })


@login_required
def gbp_metrics_daily(request, lead_pk):
    """Lista wszystkich dziennych wpisów z API z paginacją."""
    from django.core.paginator import Paginator
    from datetime import date
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')

    daily_qs = (
        lead.gbp_metrics
        .filter(source=GBPMetricsSnapshot.SOURCE_API, day__isnull=False)
        .order_by('-year', '-month', '-day')
    )

    if request.method == 'POST' and request.POST.get('action') == 'delete':
        pk = request.POST.get('pk')
        GBPMetricsSnapshot.objects.filter(pk=pk, lead=lead).delete()
        return redirect('leads:gbp_metrics_daily', lead_pk=lead.pk)

    paginator = Paginator(daily_qs, 31)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'leads/gbp_metrics/daily.html', {
        'lead': lead,
        'page': page,
        'total_count': paginator.count,
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

    # Tylko ręczne wpisy miesięczne (day=NULL)
    snapshots = lead.gbp_metrics.filter(day__isnull=True, source=GBPMetricsSnapshot.SOURCE_MANUAL)

    # Dane dzienne z API — ostatnie 30 dni
    from datetime import date
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=35)  # bufor na opóźnienie
    daily_snapshots = (
        lead.gbp_metrics
        .filter(source=GBPMetricsSnapshot.SOURCE_API, day__isnull=False)
        .filter(year__gte=thirty_days_ago.year)
        .order_by('-year', '-month', '-day')
    )
    # Filtruj po dacie w Pythonie (prosto)
    daily_snapshots = [
        s for s in daily_snapshots
        if date(s.year, s.month, s.day) >= thirty_days_ago
    ]

    # Sumy z ostatnich 30 dni
    daily_totals = {
        'calls': sum(s.calls or 0 for s in daily_snapshots),
        'profile_views': sum(s.profile_views or 0 for s in daily_snapshots),
        'website_visits': sum(s.website_visits or 0 for s in daily_snapshots),
        'direction_requests': sum(s.direction_requests or 0 for s in daily_snapshots),
        'conversations': sum(s.conversations or 0 for s in daily_snapshots),
        'bookings': sum(s.bookings or 0 for s in daily_snapshots),
        'food_orders': sum(s.food_orders or 0 for s in daily_snapshots),
        'food_menu_clicks': sum(s.food_menu_clicks or 0 for s in daily_snapshots),
        'count': len(daily_snapshots),
    }
    daily_totals['total_interactions'] = (
        daily_totals['calls'] + daily_totals['website_visits'] +
        daily_totals['direction_requests'] + daily_totals['conversations'] +
        daily_totals['bookings'] + daily_totals['food_orders'] + daily_totals['food_menu_clicks']
    )

    # Miesiące do selecta — bieżący rok i rok poprzedni
    months = [(y, m) for y in [now.year, now.year - 1] for m in range(1, 13)]
    months_choices = [
        (y, m, f"{calendar.month_name[m]} {y}")
        for y, m in months
    ]

    # Miesięczne dane z API do wykresów — ostatnie 12 miesięcy
    monthly_api = (
        lead.gbp_metrics
        .filter(source=GBPMetricsSnapshot.SOURCE_API, day__isnull=True)
        .order_by('year', 'month')
    )

    MONTHS_PL = ['', 'Sty', 'Lut', 'Mar', 'Kwi', 'Maj', 'Cze',
                 'Lip', 'Sie', 'Wrz', 'Paź', 'Lis', 'Gru']

    chart_data = {
        'labels': [f"{MONTHS_PL[s.month]} {s.year}" for s in monthly_api],
        'calls': [s.calls or 0 for s in monthly_api],
        'profile_views': [s.profile_views or 0 for s in monthly_api],
        'website_visits': [s.website_visits or 0 for s in monthly_api],
        'direction_requests': [s.direction_requests or 0 for s in monthly_api],
        'conversations': [s.conversations or 0 for s in monthly_api],
        'food_orders': [s.food_orders or 0 for s in monthly_api],
        'food_menu_clicks': [s.food_menu_clicks or 0 for s in monthly_api],
        'total_interactions': [
            (s.calls or 0) + (s.website_visits or 0) + (s.direction_requests or 0) +
            (s.conversations or 0) + (s.bookings or 0) + (s.food_orders or 0) + (s.food_menu_clicks or 0)
            for s in monthly_api
        ],
    }

    return render(request, 'leads/gbp_metrics/index.html', {
        'lead': lead,
        'snapshots': snapshots,
        'daily_snapshots': daily_snapshots,
        'daily_totals': daily_totals,
        'chart_data': json.dumps(chart_data),
        'months_choices': months_choices,
        'current_year': now.year,
        'current_month': now.month,
    })
