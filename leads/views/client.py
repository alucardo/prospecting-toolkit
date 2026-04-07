from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum
from ..models import Lead, ClientActivityLog, format_duration
from ..tasks_analysis import take_client_rank_snapshot, check_keyword_rankings


@login_required
def client_index(request):
    now = timezone.now()
    clients = (
        Lead.objects
        .filter(status='client')
        .select_related('city')
        .prefetch_related('keywords_list')
        .order_by('name')
    )

    # Działania w tym miesiącu — jedna query dla wszystkich klientów
    activities_this_month = (
        ClientActivityLog.objects
        .filter(date__year=now.year, date__month=now.month)
        .values_list('lead_id', flat=True)
    )
    activity_counts = {}
    for lead_id in activities_this_month:
        activity_counts[lead_id] = activity_counts.get(lead_id, 0) + 1

    # Działania w ostatnich 30 dniach
    thirty_days_ago = now.date() - timezone.timedelta(days=30)
    activities_30d = (
        ClientActivityLog.objects
        .filter(date__gte=thirty_days_ago)
        .values_list('lead_id', flat=True)
    )
    activity_counts_30d = {}
    for lead_id in activities_30d:
        activity_counts_30d[lead_id] = activity_counts_30d.get(lead_id, 0) + 1

    # Suma czasu w bieżącym miesiącu — jedna query
    duration_month_qs = (
        ClientActivityLog.objects
        .filter(date__year=now.year, date__month=now.month, duration_minutes__isnull=False)
        .values('lead_id')
        .annotate(total=Sum('duration_minutes'))
    )
    duration_month = {row['lead_id']: row['total'] for row in duration_month_qs}

    # Suma czasu w ostatnich 30 dniach — jedna query
    duration_30d_qs = (
        ClientActivityLog.objects
        .filter(date__gte=thirty_days_ago, duration_minutes__isnull=False)
        .values('lead_id')
        .annotate(total=Sum('duration_minutes'))
    )
    duration_30d = {row['lead_id']: row['total'] for row in duration_30d_qs}

    data = []
    for client in clients:
        data.append({
            'lead': client,
            'keywords_count': client.keywords_list.count(),
            'activities_this_month': activity_counts.get(client.pk, 0),
            'activities_30d': activity_counts_30d.get(client.pk, 0),
            'duration_month': format_duration(duration_month.get(client.pk, 0)),
            'duration_30d': format_duration(duration_30d.get(client.pk, 0)),
        })

    # Sumy globalne dla wszystkich klientów
    total_duration_month = sum(duration_month.values())
    total_duration_30d = sum(duration_30d.values())
    total_activities_month = sum(activity_counts.values())
    total_activities_30d = sum(activity_counts_30d.values())

    return render(request, 'leads/client/index.html', {
        'data': data,
        'total_duration_month': format_duration(total_duration_month),
        'total_duration_30d': format_duration(total_duration_30d),
        'total_activities_month': total_activities_month,
        'total_activities_30d': total_activities_30d,
    })


@login_required
def client_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk, status='client')
    from ..models import KeywordRankCheck, ClientRankSnapshot
    from django.utils import timezone
    import json

    # --- Dane do wykresow: wszystkie rank_checks per fraza ---
    charts = []
    for kw in lead.keywords_list.prefetch_related('rank_checks').all():
        checks = list(
            kw.rank_checks
            .order_by('checked_at')
            .values('position', 'checked_at')
        )
        if not checks:
            continue

        # Snapshoty miesięczne jako pionowe linie na wykresie
        snapshot_labels = {
            f"{s.year}-{s.month:02d}": s.label
            for s in lead.rank_snapshots.all()
        }

        charts.append({
            'phrase': kw.phrase,
            'labels': [c['checked_at'].strftime('%d.%m.%Y') for c in checks],
            'data': [c['position'] for c in checks],
            # Trend: pierwsza vs ostatnia znana pozycja
            'trend': _calc_trend(checks),
        })

    # Boksy z podsumowaniem aktywności
    from django.db.models import Sum
    from ..models import format_duration
    now_date = timezone.now().date()
    thirty_days_ago = now_date - timezone.timedelta(days=30)

    act_month = lead.activity_logs.filter(
        date__year=now_date.year, date__month=now_date.month
    )
    act_30d = lead.activity_logs.filter(date__gte=thirty_days_ago)

    activities_month = act_month.count()
    activities_30d = act_30d.count()
    duration_month = act_month.aggregate(t=Sum('duration_minutes'))['t'] or 0
    duration_30d = act_30d.aggregate(t=Sum('duration_minutes'))['t'] or 0

    # Domyślny okres raportu — cały poprzedni miesiąc
    from datetime import date
    import calendar
    first_day_this_month = now_date.replace(day=1)
    last_month_end = first_day_this_month - timezone.timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    report_from = request.GET.get('report_from') or last_month_start.strftime('%Y-%m-%d')
    report_to = request.GET.get('report_to') or last_month_end.strftime('%Y-%m-%d')
    include_keywords = request.GET.get('include_keywords', '1') == '1'
    include_metrics = request.GET.get('include_metrics', '1') == '1'
    include_activities = request.GET.get('include_activities', '1') == '1'

    return render(request, 'leads/client/detail.html', {
        'lead': lead,
        'charts_json': json.dumps(charts, ensure_ascii=False),
        'analysis': lead.business_analyses.first(),
        'activities_month': activities_month,
        'activities_30d': activities_30d,
        'duration_month': format_duration(duration_month),
        'duration_30d': format_duration(duration_30d),
        'report_from': report_from,
        'report_to': report_to,
        'include_keywords': include_keywords,
        'include_metrics': include_metrics,
        'include_activities': include_activities,
    })


def _calc_trend(checks):
    """Porownuje ostatnia vs przedostatnia znana pozycje."""
    known = [c for c in checks if c['position'] is not None]
    if len(known) < 2:
        return None
    return known[-2]['position'] - known[-1]['position']  # dodatni = lepiej


@login_required
def client_snapshot_trigger(request, pk):
    """Reczne wywolanie snapshotu dla klienta."""
    lead = get_object_or_404(Lead, pk=pk, status='client')
    if request.method == 'POST':
        take_client_rank_snapshot.delay(lead.pk, triggered_by='manual')
    return redirect('leads:client_detail', pk=pk)


@login_required
def client_check_rankings(request, pk):
    """Reczne sprawdzenie pozycji (odpala check + potem snapshot)."""
    lead = get_object_or_404(Lead, pk=pk, status='client')
    if request.method == 'POST':
        check_keyword_rankings.delay(lead.pk, force=True)
    return redirect('leads:client_detail', pk=pk)
