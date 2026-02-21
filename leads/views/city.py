from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from ..models import City, SearchQuery
from ..forms import CityForm, SearchQueryForm
from ..services.apify import run_google_maps_scraper, fetch_and_save_leads


@login_required
def city_index(request):
    cities = City.objects.annotate(
        leads_potential=Count('leads', filter=Q(leads__status__in=['new', 'no_answer', 'call_later', 'interested'])),
        leads_refused=Count('leads', filter=Q(leads__status='not_interested')),
        leads_clients=Count('leads', filter=Q(leads__status='client')),
    )
    context = {
        'cities': cities,
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
            search_query.status = status
            search_query.save()

            leads_count, leads_skipped = fetch_and_save_leads(search_query)

            return redirect('leads:city_detail', pk=city.pk)

    search_queries = city.search_queries.all().order_by('-created_at')

    context = {
        'city': city,
        'form': form,
        'search_queries': search_queries,
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
def city_delete(request, pk):
    city = City.objects.get(pk=pk)
    if request.method == 'POST':
        city.delete()
        return redirect('leads:city_index')
    return redirect('leads:city_index')