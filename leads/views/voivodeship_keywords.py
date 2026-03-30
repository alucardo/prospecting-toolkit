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
def voivodeship_keyword_debug(request, pk):
    """Diagnostyka — dwa testy: surowe API + fetch_keyword_volumes()"""
    import requests as req
    import base64
    from ..services.dataforseo_volumes import fetch_keyword_volumes

    voivodeship = get_object_or_404(Voivodeship, pk=pk)
    app_settings = AppSettings.get()

    credentials = base64.b64encode(
        f"{app_settings.dataforseo_login}:{app_settings.dataforseo_password}".encode()
    ).decode()

    test_phrases = list(
        voivodeship.keywords.filter(monthly_searches__isnull=True)
        .values_list('phrase', flat=True)[:3]
    )
    location_code = get_dataforseo_location_code(voivodeship.name)

    # Test 1: surowe API
    try:
        response = req.post(
            "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live",
            headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
            json=[{"keywords": test_phrases, "location_code": location_code, "language_name": "Polish"}],
            timeout=60,
        )
        raw = response.json()
        task = (raw.get('tasks') or [{}])[0]
        task_status = task.get('status_code')
        task_message = task.get('status_message')
        result_items = task.get('result') or []
        first_item = result_items[0] if result_items else None
        api_error = None
    except Exception as e:
        task_status = None
        task_message = None
        result_items = []
        first_item = None
        api_error = str(e)

    # Test 2: fetch_keyword_volumes() — dokładnie jak Celery task
    try:
        service_result = fetch_keyword_volumes(
            test_phrases,
            app_settings.dataforseo_login,
            app_settings.dataforseo_password,
            location_code=location_code,
        )
        service_count = len(service_result)
        service_error = None
    except Exception as e:
        service_result = {}
        service_count = 0
        service_error = str(e)

    return render(request, 'leads/voivodeship_keywords/debug.html', {
        'voivodeship': voivodeship,
        'location_code': location_code,
        'test_phrases': test_phrases,
        'task_status': task_status,
        'task_message': task_message,
        'result_count': len(result_items),
        'first_item': first_item,
        'api_error': api_error,
        'service_result': service_result,
        'service_count': service_count,
        'service_error': service_error,
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
