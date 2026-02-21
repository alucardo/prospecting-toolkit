from django.shortcuts import render, redirect, get_object_or_404
from ..models import Lead, CallLog
from ..forms import CallLogForm


def call_log_create(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    form = CallLogForm()

    if request.method == 'POST':
        form = CallLogForm(request.POST)
        if form.is_valid():
            call_log = form.save(commit=False)
            call_log.lead = lead
            call_log.save()
            return redirect('leads:lead_detail', pk=lead.pk)

    context = {
        'form': form,
        'lead': lead,
    }
    return render(request, 'leads/call_log/new.html', context)


def call_log_edit(request, pk, call_pk):
    lead = get_object_or_404(Lead, pk=pk)
    call_log = get_object_or_404(CallLog, pk=call_pk)
    form = CallLogForm(instance=call_log)

    if request.method == 'POST':
        form = CallLogForm(request.POST, instance=call_log)
        if form.is_valid():
            form.save()
            return redirect('leads:lead_detail', pk=lead.pk)

    context = {
        'form': form,
        'lead': lead,
        'call_log': call_log,
    }
    return render(request, 'leads/call_log/edit.html', context)

def call_log_delete(request, pk, call_pk):
    lead = get_object_or_404(Lead, pk=pk)
    call_log = get_object_or_404(CallLog, pk=call_pk)
    if request.method == 'POST':
        call_log.delete()
    return redirect('leads:lead_detail', pk=lead.pk)