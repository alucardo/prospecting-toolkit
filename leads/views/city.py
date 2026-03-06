from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from ..models import City, SearchQuery, Lead
from ..forms import CityForm, SearchQueryForm
from ..services.apify import run_google_maps_scraper
from ..tasks import fetch_apify_results
from .lead import DEFAULT_EXCLUDED_STATUSES


@login_required
def city_index(request):
    potential_statuses = [v for v, _ in Lead.STATUS_CHOICES if v not in DEFAULT_EXCLUDED_STATUSES]
    search = request.GET.get('search', '').strip()

    cities = City.objects.annotate(
        leads_potential=Count('leads', filter=Q(leads__status__in=potential_statuses)),
        leads_refused=Count('leads', filter=Q(leads__status='not_interested')),
        leads_clients=Count('leads', filter=Q(leads__status='client')),
    ).order_by('name')

    if search:
        cities = cities.filter(name__icontains=search)

    paginator = Paginator(cities, 25)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'cities': page,
        'total_count': paginator.count,
        'search': search,
    }
    return render(request, 'leads/city/index.html', context)


@login_required
def city_create(request):
    form = CityForm()

    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leads:city_index')

    context = {
        'form': form,
    }
    return render(request, 'leads/city/new.html', context)


@login_required
def city_detail(request, pk):
    city = City.objects.get(pk=pk)
    form = SearchQueryForm()

    if request.method == 'POST':
        form = SearchQueryForm(request.POST)
        if form.is_valid():
            search_query = form.save(commit=False)
            search_query.city = city
            search_query.status = 'running'
            search_query.save()

            run_id, status = run_google_maps_scraper(
                keyword=search_query.keyword,
                city=city.name,
                limit=search_query.limit,
            )

            search_query.apify_run_id = run_id
            search_query.status = 'pending'
            search_query.save()

            fetch_apify_results.delay(search_query.pk)

            return redirect('leads:city_detail', pk=city.pk)

    search_queries = city.search_queries.all().order_by('-created_at')
    leads_count = city.leads.exclude(status='rejected').count()

    context = {
        'city': city,
        'form': form,
        'search_queries': search_queries,
        'leads_count': leads_count,
    }
    return render(request, 'leads/city/detail.html', context)

@login_required
def city_edit(request, pk):
    city = City.objects.get(pk=pk)
    form = CityForm(instance=city)

    if request.method == 'POST':
        form = CityForm(request.POST, instance=city)
        if form.is_valid():
            form.save()
            return redirect('leads:city_index')

    context = {
        'form': form,
        'city': city,
    }
    return render(request, 'leads/city/edit.html', context)


@login_required
def city_geocode(request):
    """Uzupelnia wspolrzedne dla miast ktore ich nie maja przez Nominatim."""
    import requests as req
    from django.contrib import messages

    cities_without = City.objects.filter(latitude__isnull=True)
    updated = 0
    failed = []

    for city in cities_without:
        try:
            resp = req.get(
                'https://nominatim.openstreetmap.org/search',
                params={'q': f"{city.name}, Poland", 'format': 'json', 'limit': 1},
                headers={'User-Agent': 'ProspectingToolkit/1.0'},
                timeout=5,
            )
            resp.raise_for_status()
            results = resp.json()
            if results:
                city.latitude = float(results[0]['lat'])
                city.longitude = float(results[0]['lon'])
                city.save()
                updated += 1
            else:
                failed.append(city.name)
        except Exception:
            failed.append(city.name)

    if updated:
        messages.success(request, f'Uzupelniono wspolrzedne dla {updated} miast.')
    if failed:
        messages.warning(request, f'Nie udalo sie uzupelnic: {", ".join(failed)}')
    if not updated and not failed:
        messages.info(request, 'Wszystkie miasta maja juz wspolrzedne.')

    return redirect('leads:city_index')


@login_required
def city_delete(request, pk):
    city = City.objects.get(pk=pk)
    if request.method == 'POST':
        city.delete()
        return redirect('leads:city_index')
    return redirect('leads:city_index')