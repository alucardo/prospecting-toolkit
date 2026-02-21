from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.postgres.search import TrigramSimilarity
from ..models import Lead
from ..forms import LeadForm


def lead_index(request):
    show_rejected = request.GET.get('show_rejected') == '1'
    search = request.GET.get('search', '').strip()

    leads = Lead.objects.select_related('city').annotate(
        call_count=Count('call_logs')
    ).order_by('-created_at')

    if not show_rejected:
        leads = leads.exclude(status='rejected')

    if search:
        leads = leads.annotate(
            similarity=TrigramSimilarity('name', search)
        ).filter(
            Q(name__icontains=search) |
            Q(address__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(similarity__gt=0.1)
        ).order_by('-similarity')

    context = {
        'leads': leads,
        'show_rejected': show_rejected,
        'search': search,
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
    call_logs = lead.call_logs.all().order_by('-called_at')
    context = {
        'lead': lead,
        'call_logs': call_logs,
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


def lead_bulk_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_leads')

        if action == 'reject' and selected_ids:
            Lead.objects.filter(pk__in=selected_ids).update(status='rejected')

    return redirect('leads:lead_index')
