from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Lead, LeadStatusHistory


@login_required
def lead_status_history_delete(request, pk, history_pk):
    lead = get_object_or_404(Lead, pk=pk)
    entry = get_object_or_404(LeadStatusHistory, pk=history_pk, lead=lead)
    if request.method == 'POST':
        entry.delete()
    return redirect('leads:lead_detail', pk=lead.pk)
