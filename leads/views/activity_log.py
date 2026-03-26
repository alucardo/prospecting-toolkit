from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Lead, ClientActivityLog
from ..forms import ClientActivityLogForm


@login_required
def activity_log_index(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    logs = lead.activity_logs.select_related('user').all()

    # Filtr miesiąca
    month = request.GET.get('month')  # format: 2025-03
    if month:
        try:
            year, m = month.split('-')
            logs = logs.filter(date__year=year, date__month=m)
        except ValueError:
            pass

    form = ClientActivityLogForm(initial={'date': timezone.now().date()})

    if request.method == 'POST':
        form = ClientActivityLogForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.lead = lead
            entry.user = request.user
            entry.save()
            return redirect('leads:activity_log_index', lead_pk=lead.pk)

    return render(request, 'leads/activity_log/index.html', {
        'lead': lead,
        'logs': logs,
        'form': form,
        'month': month,
    })


@login_required
def activity_log_edit(request, lead_pk, pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    log = get_object_or_404(ClientActivityLog, pk=pk, lead=lead)
    form = ClientActivityLogForm(instance=log)

    if request.method == 'POST':
        form = ClientActivityLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            return redirect('leads:activity_log_index', lead_pk=lead.pk)

    return render(request, 'leads/activity_log/edit.html', {
        'lead': lead,
        'log': log,
        'form': form,
    })


@login_required
def activity_log_delete(request, lead_pk, pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    log = get_object_or_404(ClientActivityLog, pk=pk, lead=lead)
    if request.method == 'POST':
        log.delete()
    return redirect('leads:activity_log_index', lead_pk=lead.pk)
