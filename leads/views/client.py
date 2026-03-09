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
    snapshots = lead.rank_snapshots.all()  # ordering: -year, -month

    # Buduj macierz: frazy × miesiace dla tabeli porownawczej
    all_phrases = list(lead.keywords_list.values_list('phrase', flat=True))

    # Ostatnie 6 snapshotow (wystarczy do tabeli)
    recent_snapshots = list(snapshots[:6])

    # Buduj wiersze tabeli: [{phrase, trend, cells: [pos, pos, ...]}, ...]
    rows = []
    for phrase in all_phrases:
        cells = []
        for snap in recent_snapshots:
            pos = next(
                (item['position'] for item in snap.positions if item['phrase'] == phrase),
                None
            )
            cells.append(pos)

        # Trend: ostatni vs poprzedni snapshot
        trend = None
        if len(cells) >= 2 and cells[0] is not None and cells[1] is not None:
            trend = cells[1] - cells[0]  # dodatni = poprawil sie (mniejszy nr = lepsza pozycja)

        rows.append({'phrase': phrase, 'trend': trend, 'cells': cells})

    return render(request, 'leads/client/detail.html', {
        'lead': lead,
        'snapshots': recent_snapshots,
        'rows': rows,
        'analysis': lead.business_analyses.first(),
    })


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
        check_keyword_rankings.delay(lead.pk)
    return redirect('leads:client_detail', pk=pk)
