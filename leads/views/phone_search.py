from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from leads.models import Lead, LeadContact
import re


@login_required
def phone_search(request):
    q = request.GET.get('q', '').strip()

    if not q:
        return redirect('leads:lead_index')

    # Normalizuj numer - zostaw tylko cyfry
    digits = re.sub(r'\D', '', q)

    if not digits:
        return render(request, 'leads/phone_search.html', {'q': q, 'leads': [], 'error': 'Podaj numer telefonu.'})

    phone_regex = r'[\s\-\.]?'.join(digits)

    # Szukaj po numerze głównym leada
    leads_by_phone = Lead.objects.filter(
        phone__iregex=phone_regex
    ).select_related('city')

    # Szukaj w osobach kontaktowych przypisanych do leada
    contact_lead_ids = LeadContact.objects.filter(
        phone__iregex=phone_regex
    ).values_list('lead_id', flat=True)

    leads_by_contact = Lead.objects.filter(
        pk__in=contact_lead_ids
    ).select_related('city')

    # Połącz i deduplikuj
    leads = (leads_by_phone | leads_by_contact).distinct()

    if leads.count() == 1:
        return redirect('leads:lead_detail', pk=leads.first().pk)

    return render(request, 'leads/phone_search.html', {'q': q, 'leads': leads})
