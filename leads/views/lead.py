from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q
from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from ..models import Lead, City, LeadStatusHistory, VoivodeshipKeyword
from ..forms import LeadForm, LeadNoteForm, LeadContactForm


DEFAULT_EXCLUDED_STATUSES = {'rejected', 'close', 'not_interested', 'client', 'complete_profile', 'left_contact'}

@login_required
def lead_index(request):
    search = request.GET.get('search', '').strip()
    city_filter = request.GET.get('city', '')
    email_filter = request.GET.get('email_filter', '')

    # Jesli uzytkownik nie wyslal zadnego filtra statusu, domyslnie zaznacz wszystkie poza wykluczonymi
    all_status_values = {v for v, _ in Lead.STATUS_CHOICES}
    default_statuses = sorted(all_status_values - DEFAULT_EXCLUDED_STATUSES)

    if 'status' in request.GET:
        status_filter = request.GET.getlist('status')
    else:
        status_filter = default_statuses

    leads = Lead.objects.select_related('city').annotate(
        call_count=Count('call_logs')
    ).order_by('-created_at')

    if city_filter:
        leads = leads.filter(city__pk=city_filter)

    if status_filter:
        leads = leads.filter(status__in=status_filter)

    if email_filter == 'to_scrape':
        leads = leads.filter(
            website__isnull=False,
            email_scraped=False,
            email='',
        ).exclude(website='').exclude(
            website__icontains='facebook.com'
        ).exclude(
            website__icontains='fb.com'
        )

    if search:
        leads = leads.annotate(
            similarity=TrigramSimilarity('name', search)
        ).filter(
            Q(name__icontains=search) |
            Q(address__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(similarity__gt=0.1)
        ).order_by('-similarity')

    cities = City.objects.all().order_by('name')

    paginator = Paginator(leads, 20)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    # Jedno zapytanie dla przypomnień — tylko leady z bieżącej strony
    from django.utils import timezone
    from ..models import CallLog
    lead_pks = [lead.pk for lead in page]
    reminders_qs = (
        CallLog.objects
        .filter(
            lead_id__in=lead_pks,
            is_reminder_active=True,
            next_contact_date__isnull=False,
        )
        .order_by('lead_id', 'next_contact_date')
        .values('lead_id', 'next_contact_date')
    )
    # Bierzemy najwcześniejszy reminder per lead
    next_contact_map = {}
    for row in reminders_qs:
        lid = row['lead_id']
        if lid not in next_contact_map:
            next_contact_map[lid] = row['next_contact_date']

    now = timezone.now()

    # Doklejamy next_contact_date bezposrednio do obiektu — zero N+1
    for lead in page:
        lead.next_contact = next_contact_map.get(lead.pk)

    context = {
        'leads': page,
        'total_count': paginator.count,
        'search': search,
        'cities': cities,
        'city_filter': city_filter,
        'status_filter': status_filter,
        'status_choices': Lead.STATUS_CHOICES,
        'email_filter': email_filter,
        'default_excluded_statuses': DEFAULT_EXCLUDED_STATUSES,
        'next_contact_map': next_contact_map,
        'now': now,
    }
    return render(request, 'leads/lead/index.html', context)


@login_required
def lead_create(request):
    form = LeadForm()
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leads:lead_index')
    context = {
        'form': form,
    }
    return render(request, 'leads/lead/new.html', context)


@login_required
def lead_detail(request, pk):
    lead = Lead.objects.get(pk=pk)
    call_logs = lead.call_logs.all().order_by('-called_at')
    note_form = LeadNoteForm()
    contact_form = LeadContactForm()

    full_history = request.GET.get('full_history') == '1'
    status_history_qs = lead.status_history.select_related('user').order_by('-changed_at')
    status_history = status_history_qs if full_history else status_history_qs[:5]
    status_history_count = status_history_qs.count()

    # Wolumeny fraz z województwa leada
    voivodeship = lead.city.voivodeship if lead.city else None
    keyword_volumes = {}
    if voivodeship:
        vkws = VoivodeshipKeyword.objects.filter(
            voivodeship=voivodeship,
            phrase__in=lead.keywords_list.values_list('phrase', flat=True)
        )
        keyword_volumes = {vkw.phrase: vkw.monthly_searches for vkw in vkws}

    # Dodaj wolumen bezposrednio do obiektow fraz (unikamy template trickow)
    keywords_with_volume = []
    keywords_with_position = []
    for kw in lead.keywords_list.all().prefetch_related('rank_checks'):
        kw.monthly_searches = keyword_volumes.get(kw.phrase)
        keywords_with_volume.append(kw)
        last_check = kw.rank_checks.first()
        keywords_with_position.append({
            'pk': kw.pk,
            'phrase': kw.phrase,
            'position': last_check.position if last_check else None,
        })

    # Następny krok w pipeline
    next_pipeline_step = None
    if hasattr(lead, 'pipeline_entry'):
        entry = lead.pipeline_entry
        next_pipeline_step = entry.pipeline.steps.filter(
            order__gt=entry.current_step.order
        ).order_by('order').first()

    from ..models import LeadCategory
    all_categories = LeadCategory.objects.all()

    context = {
        'lead': lead,
        'call_logs': call_logs,
        'note_form': note_form,
        'status_history': status_history,
        'status_history_count': status_history_count,
        'full_history': full_history,
        'contact_form': contact_form,
        'keywords_with_volume': keywords_with_volume,
        'keywords_with_position': keywords_with_position,
        'next_pipeline_step': next_pipeline_step,
        'all_categories': all_categories,
    }
    return render(request, 'leads/lead/detail.html', context)


@login_required
def lead_edit(request, pk):
    lead = Lead.objects.get(pk=pk)
    old_status = lead.status
    form = LeadForm(instance=lead)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            if old_status != new_status:
                LeadStatusHistory.objects.create(
                    lead=lead,
                    user=request.user,
                    status=new_status,
                )
            form.save()
            return redirect('leads:lead_detail', pk=lead.pk)
    context = {
        'form': form,
        'lead': lead,
    }
    return render(request, 'leads/lead/edit.html', context)


@login_required
def lead_delete(request, pk):
    lead = Lead.objects.get(pk=pk)
    if request.method == 'POST':
        lead.delete()
        return redirect('leads:lead_index')
    return redirect('leads:lead_index')


from ..tasks import scrape_lead_email, scrape_leads_emails_bulk


@login_required
def lead_quick_note(request, pk):
    """AJAX — zapisuje szybką notatkę do leada."""
    from django.http import JsonResponse
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        note = request.POST.get('quick_note', '').strip()
        lead.quick_note = note
        lead.save(update_fields=['quick_note'])
        return JsonResponse({'ok': True, 'quick_note': lead.quick_note})
    return JsonResponse({'error': 'method not allowed'}, status=405)


@login_required
def lead_geocode(request, pk):
    """AJAX — wyznacza GPS lokalu przez Google Geocoding API."""
    from django.http import JsonResponse
    import requests as req
    lead = get_object_or_404(Lead, pk=pk)

    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    from ..models import AppSettings
    settings = AppSettings.get()
    api_key = settings.google_maps_api_key or ''

    # Zbuduj adres do geocodingu
    address_parts = []
    if lead.address:
        address_parts.append(lead.address)
    if lead.city:
        address_parts.append(lead.city.name)
    address_parts.append('Poland')
    address = ', '.join(address_parts)

    try:
        params = {'address': address, 'key': api_key}
        resp = req.get(
            'https://maps.googleapis.com/maps/api/geocode/json',
            params=params,
            timeout=10,
        )
        data = resp.json()
        if data.get('status') != 'OK' or not data.get('results'):
            return JsonResponse({'error': f'Geocoding nie znałazł adresu: {address}. Status: {data.get("status")}'})

        location = data['results'][0]['geometry']['location']
        lat = location['lat']
        lng = location['lng']
        formatted = data['results'][0].get('formatted_address', address)

        # Zapisz do bazy
        lead.latitude = lat
        lead.longitude = lng
        lead.save(update_fields=['latitude', 'longitude'])

        return JsonResponse({
            'ok': True,
            'lat': lat,
            'lng': lng,
            'formatted_address': formatted,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def lead_scrape_email(request, pk):
    lead = Lead.objects.get(pk=pk)
    if request.method == 'POST':
        scrape_lead_email.delay(lead.pk)
    return redirect('leads:lead_detail', pk=lead.pk)


@login_required
def lead_bulk_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_leads')

        if action == 'reject' and selected_ids:
            Lead.objects.filter(pk__in=selected_ids).update(status='rejected')

        if action == 'scrape_emails' and selected_ids:
            scrape_leads_emails_bulk.delay(selected_ids)

    return redirect('leads:lead_index')
