from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db import models
from django.utils import timezone
from ..models import Voivodeship, VoivodeshipKeyword, AppSettings
from ..constants import get_dataforseo_location_code


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
    stale_threshold = timezone.now() - timezone.timedelta(days=30)
    # Wszystkie frazy bez wartości — do pokazania przycisku
    missing_count = keywords.filter(monthly_searches__isnull=True).count()
    # Z nich: ile faktycznie zostanie wysłanych do API (nie sprawdzane w ciągu 30 dni)
    fetchable_count = keywords.filter(
        monthly_searches__isnull=True,
    ).filter(
        models.Q(searches_updated_at__isnull=True) |
        models.Q(searches_updated_at__lt=stale_threshold)
    ).count()
    # Frazy bez wolumenu ale już sprawdzane (DataForSEO nie znał) — do info
    checked_no_data = keywords.filter(
        monthly_searches__isnull=True,
        searches_updated_at__isnull=False,
        searches_updated_at__gte=stale_threshold,
    ).count()
    return render(request, 'leads/voivodeship_keywords/detail.html', {
        'voivodeship': voivodeship,
        'keywords': keywords,
        'missing_count': missing_count,
        'fetchable_count': fetchable_count,
        'checked_no_data': checked_no_data,
        'dataforseo_location': f"{get_dataforseo_location_code(voivodeship.name)} ({voivodeship.name})",
    })


@login_required
def voivodeship_keyword_fetch_volumes(request, pk):
    """Pobiera wolumeny wyszukań z DataForSEO dla fraz bez wartości."""
    voivodeship = get_object_or_404(Voivodeship, pk=pk)

    if request.method != 'POST':
        return redirect('leads:voivodeship_keyword_detail', pk=pk)

    app_settings = AppSettings.get()
    if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
        return redirect('leads:voivodeship_keyword_detail', pk=pk)

    # Odpal task Celery w tle — gunicorn nie czeka, uzytkownik dostaje natychmiastowy redirect
    from ..tasks import fetch_keyword_volumes_task
    fetch_keyword_volumes_task.delay(voivodeship.pk)

    return redirect('leads:voivodeship_keyword_detail', pk=pk)
