from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ..models import Lead
from ..tasks_analysis import take_client_rank_snapshot, check_keyword_rankings


@login_required
def client_index(request):
    clients = (
        Lead.objects
        .filter(status='client')
        .select_related('city')
        .prefetch_related('business_analyses', 'keywords_list')
        .order_by('name')
    )

    data = []
    for client in clients:
        analysis = client.business_analyses.first()
        data.append({
            'lead': client,
            'analysis': analysis,
            'has_maps_url': bool(client.google_maps_url),
            'keywords_count': client.keywords_list.count(),
        })

    return render(request, 'leads/client/index.html', {'data': data})


@login_required
def client_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk, status='client')
    from ..models import KeywordRankCheck, ClientRankSnapshot
    from django.utils import timezone
    import json

    # --- Tabela snapshotow miesiecznych ---
    recent_snapshots = list(lead.rank_snapshots.all()[:6])
    all_phrases = list(lead.keywords_list.values_list('phrase', flat=True))

    rows = []
    for phrase in all_phrases:
        cells = []
        for snap in recent_snapshots:
            pos = next(
                (item['position'] for item in snap.positions if item['phrase'] == phrase),
                None
            )
            cells.append(pos)

        trend = None
        if len(cells) >= 2 and cells[0] is not None and cells[1] is not None:
            trend = cells[1] - cells[0]

        rows.append({'phrase': phrase, 'trend': trend, 'cells': cells})

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
        'snapshots': recent_snapshots,
        'rows': rows,
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
