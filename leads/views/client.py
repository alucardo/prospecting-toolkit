from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from ..models import Lead, ClientActivityLog
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

    data = []
    for client in clients:
        data.append({
            'lead': client,
            'keywords_count': client.keywords_list.count(),
            'activities_this_month': activity_counts.get(client.pk, 0),
            'activities_30d': activity_counts_30d.get(client.pk, 0),
        })

    return render(request, 'leads/client/index.html', {'data': data})


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

    return render(request, 'leads/client/detail.html', {
        'lead': lead,
        'charts_json': json.dumps(charts, ensure_ascii=False),
        'analysis': lead.business_analyses.first(),
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
