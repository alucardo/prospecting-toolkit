from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Lead, LeadContact
from ..forms import LeadContactForm


@login_required
def lead_contact_create(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.lead = lead
            contact.save()
    return redirect('leads:lead_detail', pk=lead.pk)


@login_required
def lead_contact_edit(request, pk, contact_pk):
    lead = get_object_or_404(Lead, pk=pk)
    contact = get_object_or_404(LeadContact, pk=contact_pk, lead=lead)
    if request.method == 'POST':
        form = LeadContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            return redirect('leads:lead_detail', pk=lead.pk)
    else:
        form = LeadContactForm(instance=contact)
    return render(request, 'leads/lead/contact_edit.html', {'form': form, 'lead': lead, 'contact': contact})


@login_required
def lead_contact_delete(request, pk, contact_pk):
    lead = get_object_or_404(Lead, pk=pk)
    contact = get_object_or_404(LeadContact, pk=contact_pk, lead=lead)
    if request.method == 'POST':
        contact.delete()
    return redirect('leads:lead_detail', pk=lead.pk)
