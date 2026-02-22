from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from leads.models import Lead, GoogleBusinessAnalysis
from leads.tasks_analysis import fetch_google_business_data, run_google_business_analysis


@login_required
def google_business_fetch(request, pk):
    """Krok 1: Pobierz dane z DataForSEO."""
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        # Natychmiast tworzy rekord - uzytkownik od razu widzi spinner
        placeholder = GoogleBusinessAnalysis.objects.create(
            lead=lead,
            status='pending',
        )
        fetch_google_business_data.delay(lead.pk, analysis_id=placeholder.pk)
    return redirect('leads:lead_detail', pk=pk)


@login_required
def google_business_analyze(request, pk):
    """Krok 2: Uruchom analize AI na pobranych danych."""
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        analysis = lead.business_analyses.filter(status='fetched').first()
        if not analysis:
            messages.error(request, 'Brak pobranych danych. Najpierw pobierz dane z Google.')
            return redirect('leads:lead_detail', pk=pk)
        raw = request.POST.get('keywords', '').strip()
        keywords = [k.strip() for k in raw.split(',') if k.strip()] if raw else list(lead.keywords_list.values_list('phrase', flat=True))
        run_google_business_analysis.delay(analysis.pk, keywords=keywords)
        messages.info(request, 'Analiza AI zostala uruchomiona. Odswiez strone za chwile.')
    return redirect('leads:lead_detail', pk=pk)
