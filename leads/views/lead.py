from django.shortcuts import render, redirect
from ..models import Lead
from ..forms import LeadForm


def lead_index(request):
    leads = Lead.objects.select_related('city').order_by('-created_at')
    context = {
        'leads': leads,
    }
    return render(request, 'leads/lead/index.html', context)


def lead_create(request):
    form = LeadForm()
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leads:lead_index')
    context = {
        'form': form,
    }
    return render(request, 'leads/lead/new.html', context)

def lead_detail(request, pk):
    lead = Lead.objects.get(pk=pk)
    context = {
        'lead': lead,
    }
    return render(request, 'leads/lead/detail.html', context)

def lead_edit(request, pk):
    lead = Lead.objects.get(pk=pk)
    form = LeadForm(instance=lead)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            return redirect('leads:lead_index')
    context = {
        'form': form,
        'lead': lead,
    }
    return render(request, 'leads/lead/edit.html', context)


def lead_delete(request, pk):
    lead = Lead.objects.get(pk=pk)
    if request.method == 'POST':
        lead.delete()
        return redirect('leads:lead_index')
    return redirect('leads:lead_index')