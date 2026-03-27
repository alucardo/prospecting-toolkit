from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db import models
from django.utils import timezone
from ..models import Voivodeship, VoivodeshipKeyword, AppSettings
from ..services.dataforseo_volumes import fetch_keyword_volumes
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

    # Pobieramy wszystkie frazy bez wartości — użytkownik kliknął przycisk świadomie.
    # Cooldown 30 dni chroni tylko frazy które DataForSEO już sprawdził i NIE znał
    # (monthly_searches IS NULL ale searches_updated_at ustawione niedawno).
    # Tutaj resetujemy searches_updated_at dla takich fraz, żeby wymusić ponowne sprawdzenie.
    stale_threshold = timezone.now() - timezone.timedelta(days=30)
    keywords_to_update = list(
        voivodeship.keywords.filter(monthly_searches__isnull=True)
    )
    # Reset daty dla fraz które były sprawdzane z błędnym endpointem
    # (mają searches_updated_at ale brak wartości) — wymuszamy ponowne pobranie
    voivodeship.keywords.filter(
        monthly_searches__isnull=True,
        searches_updated_at__isnull=False,
    ).update(searches_updated_at=None)

    if not keywords_to_update:
        return redirect('leads:voivodeship_keyword_detail', pk=pk)

    phrases = [kw.phrase for kw in keywords_to_update]
    location_code = get_dataforseo_location_code(voivodeship.name)
    volumes = fetch_keyword_volumes(
        phrases,
        app_settings.dataforseo_login,
        app_settings.dataforseo_password,
        location_code=location_code,
    )

    now = timezone.now()
    updated = 0
    for kw in keywords_to_update:
        volume = volumes.get(kw.phrase)
        if volume is not None:
            # DataForSEO zna wolumin — zapisz wartość i datę
            kw.monthly_searches = str(volume)
            kw.searches_updated_at = now
            kw.save(update_fields=['monthly_searches', 'searches_updated_at'])
            updated += 1
        else:
            # DataForSEO nie ma danych dla tej frazy — zapisz samą datę sprawdzenia
            # dzięki temu nie będziemy płacić za nią przy każdym kliknięciu
            kw.searches_updated_at = now
            kw.save(update_fields=['searches_updated_at'])

    return redirect('leads:voivodeship_keyword_detail', pk=pk)
