from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from leads.models import Lead, KeywordSuggestionBatch, LeadKeyword
from leads.tasks_analysis import generate_keyword_suggestions


@login_required
def keyword_suggestions(request, pk):
    from django.utils import timezone
    from datetime import timedelta
    lead = get_object_or_404(Lead, pk=pk)
    latest_batch = lead.suggestion_batches.first()

    # Jesli batch utknął w pending dłużej niż 3 minuty — oznacz jako error
    if latest_batch and latest_batch.status == 'pending':
        age = timezone.now() - latest_batch.created_at
        if age > timedelta(minutes=3):
            latest_batch.status = 'error'
            latest_batch.error_message = 'Przekroczono limit czasu. Zadanie prawdopodobnie nie zostało ukończone (sprawdź czy Celery działa).'
            latest_batch.save()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'generate':
            batch = KeywordSuggestionBatch.objects.create(lead=lead, status='pending')
            generate_keyword_suggestions.delay(lead.pk, batch.pk)
            return redirect('leads:keyword_suggestions', pk=pk)

        if action == 'add_selected':
            phrase_ids = request.POST.getlist('phrases')
            if latest_batch:
                for suggestion in latest_batch.suggestions.filter(pk__in=phrase_ids):
                    LeadKeyword.objects.get_or_create(lead=lead, phrase=suggestion.phrase)
            messages.success(request, f'Dodano {len(phrase_ids)} fraz do leada.')
            return redirect('leads:lead_detail', pk=pk)

    # Zbior fraz juz dodanych do leada (do oznaczania w tabeli)
    added_phrases = set(lead.keywords_list.values_list('phrase', flat=True))

    return render(request, 'leads/lead/keyword_suggestions.html', {
        'lead': lead,
        'batch': latest_batch,
        'added_phrases': added_phrases,
    })
