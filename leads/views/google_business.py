from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from leads.models import Lead
from leads.tasks_analysis import analyze_google_business


@login_required
def google_business_analyze(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        analyze_google_business.delay(lead.pk)
        messages.info(request, 'Analiza wizytówki została uruchomiona. Odśwież stronę za chwilę.')
    return redirect('leads:lead_detail', pk=pk)
