from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from leads.models import Lead, City, AppSettings
from leads.tasks_analysis import extract_keyword_from_maps_url, get_dataforseo_business_data, extract_business_data


@login_required
def lead_import_from_maps(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # KROK 1: pobierz dane z DataForSEO
        if action == 'fetch':
            maps_url = request.POST.get('maps_url', '').strip()
            if not maps_url:
                messages.error(request, 'Podaj link do wizytówki.')
                return render(request, 'leads/lead/import_from_maps.html', {})

            app_settings = AppSettings.get()
            if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
                messages.error(request, 'Brak konfiguracji DataForSEO w ustawieniach.')
                return render(request, 'leads/lead/import_from_maps.html', {})

            try:
                keyword_override = extract_keyword_from_maps_url(maps_url)
                # Potrzebujemy seed do wyszukiwania - bez CID szukamy po URL
                # Wyciagnij nazwe z URL jesli mozliwe
                import re
                name_from_url = ''
                match = re.search(r'/place/([^/@]+)', maps_url)
                if match:
                    name_from_url = match.group(1).replace('+', ' ').replace('%20', ' ')

                result = get_dataforseo_business_data(
                    name_from_url or 'firma',
                    '',
                    app_settings.dataforseo_login,
                    app_settings.dataforseo_password,
                    keyword_override=keyword_override,
                )
                items = result.get('tasks', [{}])[0].get('result', [{}])[0].get('items', [])

                if not items:
                    messages.error(request, 'Nie znaleziono wizytówki. Sprawdź link.')
                    return render(request, 'leads/lead/import_from_maps.html', {'maps_url': maps_url})

                biz = items[0]
                data = extract_business_data(biz)

                # Wyciagnij adres i miasto z raw data
                address_full = biz.get('address', '') or ''
                address_detail = biz.get('address_info', {}) or {}
                city_name = address_detail.get('city', '') or ''
                address_street = address_detail.get('address', '') or address_full

                preview = {
                    'maps_url': maps_url,
                    'name': data.get('business_name', ''),
                    'phone': biz.get('phone', '') or '',
                    'website': data.get('website_url', '') or '',
                    'address': address_street,
                    'city_name': city_name,
                    'rating': data.get('rating', ''),
                    'category': data.get('primary_category', ''),
                    'description': data.get('description', '')[:200] if data.get('description') else '',
                }

                # Sprobuj dopasowac miasto z bazy
                matched_city = None
                if city_name:
                    matched_city = City.objects.filter(name__iexact=city_name).first()

                return render(request, 'leads/lead/import_from_maps.html', {
                    'preview': preview,
                    'matched_city': matched_city,
                })

            except Exception as e:
                messages.error(request, f'Błąd pobierania danych: {e}')
                return render(request, 'leads/lead/import_from_maps.html', {'maps_url': request.POST.get('maps_url', '')})

        # KROK 2: utwórz leada
        if action == 'create':
            city_id = request.POST.get('city_id')
            city_name_new = request.POST.get('city_name_new', '').strip()

            if city_id:
                city = City.objects.get(pk=city_id)
            elif city_name_new:
                city, _ = City.objects.get_or_create(name=city_name_new)
            else:
                messages.error(request, 'Wybierz lub wpisz miasto.')
                return redirect('leads:lead_import_from_maps')

            lead = Lead.objects.create(
                city=city,
                name=request.POST.get('name', '').strip(),
                phone=request.POST.get('phone', '').strip(),
                website=request.POST.get('website', '').strip(),
                address=request.POST.get('address', '').strip(),
                google_maps_url=request.POST.get('maps_url', '').strip(),
                source=Lead.SOURCE_GOOGLE_MAPS,
                status=Lead.STATUS_NEW,
            )
            messages.success(request, f'Lead "{lead.name}" został dodany.')
            return redirect('leads:lead_detail', pk=lead.pk)

    return render(request, 'leads/lead/import_from_maps.html', {})
