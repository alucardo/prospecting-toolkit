from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from leads.models import Lead, LeadKeyword


@login_required
def lead_keyword_add(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        phrase = request.POST.get('phrase', '').strip()
        if phrase:
            LeadKeyword.objects.get_or_create(lead=lead, phrase=phrase)
    return redirect('leads:lead_detail', pk=pk)


@login_required
def lead_keyword_delete(request, lead_pk, keyword_pk):
    keyword = get_object_or_404(LeadKeyword, pk=keyword_pk, lead_id=lead_pk)
    if request.method == 'POST':
        keyword.delete()
    return redirect('leads:lead_detail', pk=lead_pk)
