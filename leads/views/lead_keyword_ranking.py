from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from leads.models import Lead
from leads.tasks_analysis import check_keyword_rankings


@login_required
def lead_keyword_check_rankings(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        check_keyword_rankings.delay(lead.pk)
    return redirect('leads:lead_detail', pk=pk)


@login_required
def lead_keyword_check_single(request, lead_pk, keyword_pk):
    from leads.models import LeadKeyword
    keyword = get_object_or_404(LeadKeyword, pk=keyword_pk, lead_id=lead_pk)
    if request.method == 'POST':
        check_keyword_rankings.delay(lead_pk, keyword_ids=[keyword_pk])
    return redirect('leads:lead_detail', pk=lead_pk)
