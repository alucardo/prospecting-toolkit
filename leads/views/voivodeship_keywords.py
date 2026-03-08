from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Voivodeship, VoivodeshipKeyword


@login_required
def voivodeship_keyword_index(request):
    """Lista województw z liczbą fraz."""
    voivodeships = Voivodeship.objects.prefetch_related('keywords').all()
    data = []
    for v in voivodeships:
        kw = v.keywords.all()
        data.append({
            'voivodeship': v,
            'total': kw.count(),
            'with_volume': kw.filter(monthly_searches__isnull=False).count(),
        })
    return render(request, 'leads/voivodeship_keywords/index.html', {'data': data})


@login_required
def voivodeship_keyword_detail(request, pk):
    """Lista fraz dla danego województwa z możliwością edycji monthly_searches."""
    voivodeship = get_object_or_404(Voivodeship, pk=pk)

    if request.method == 'POST':
        # Zapisz wszystkie nadesłane wartości naraz
        updated = 0
        for key, value in request.POST.items():
            if key.startswith('searches_'):
                kw_id = key.replace('searches_', '')
                try:
                    kw = VoivodeshipKeyword.objects.get(pk=kw_id, voivodeship=voivodeship)
                    new_val = value.strip() or None
                    if kw.monthly_searches != new_val:
                        kw.monthly_searches = new_val
                        kw.searches_updated_at = timezone.now() if new_val is not None else None
                        kw.save(update_fields=['monthly_searches', 'searches_updated_at'])
                        updated += 1
                except VoivodeshipKeyword.DoesNotExist:
                    pass
        return redirect('leads:voivodeship_keyword_detail', pk=pk)

    keywords = voivodeship.keywords.all()
    return render(request, 'leads/voivodeship_keywords/detail.html', {
        'voivodeship': voivodeship,
        'keywords': keywords,
    })
