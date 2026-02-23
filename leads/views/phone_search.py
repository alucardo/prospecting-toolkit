from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from leads.models import Lead
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

    # Szukaj po numerze - ignoruj formatowanie (spacje, myślniki itp.)
    leads = Lead.objects.filter(phone__iregex=r'[\s\-\.]?'.join(digits)).select_related('city')

    if leads.count() == 1:
        return redirect('leads:lead_detail', pk=leads.first().pk)

    return render(request, 'leads/phone_search.html', {'q': q, 'leads': leads})
