from django.shortcuts import render, redirect
from django.db.models import Count, Q
from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from ..models import Lead, City, LeadStatusHistory
from ..forms import LeadForm, LeadNoteForm


@login_required
def lead_index(request):
    show_rejected = request.GET.get('show_rejected') == '1'
    search = request.GET.get('search', '').strip()
    city_filter = request.GET.get('city', '')
    status_filter = request.GET.getlist('status')
    email_filter = request.GET.get('email_filter', '')

    leads = Lead.objects.select_related('city').annotate(
        call_count=Count('call_logs')
    ).order_by('-created_at')

    if not show_rejected:
        leads = leads.exclude(status='rejected')

    if city_filter:
        leads = leads.filter(city__pk=city_filter)

    if status_filter:
        leads = leads.filter(status__in=status_filter)

    if email_filter == 'to_scrape':
        leads = leads.filter(
            website__isnull=False,
            email_scraped=False,
            email='',
        ).exclude(website='').exclude(
            website__icontains='facebook.com'
        ).exclude(
            website__icontains='fb.com'
        )

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

    cities = City.objects.all()

    paginator = Paginator(leads, 20)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        'leads': page,
        'total_count': paginator.count,
        'show_rejected': show_rejected,
        'search': search,
        'cities': cities,
        'city_filter': city_filter,
        'status_filter': status_filter,
        'status_choices': Lead.STATUS_CHOICES,
        'email_filter': email_filter,
    }
    return render(request, 'leads/lead/index.html', context)


@login_required
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


@login_required
def lead_detail(request, pk):
    lead = Lead.objects.get(pk=pk)
    call_logs = lead.call_logs.all().order_by('-called_at')
    note_form = LeadNoteForm()

    full_history = request.GET.get('full_history') == '1'
    status_history_qs = lead.status_history.select_related('user').order_by('-changed_at')
    status_history = status_history_qs if full_history else status_history_qs[:5]
    status_history_count = status_history_qs.count()

    context = {
        'lead': lead,
        'call_logs': call_logs,
        'note_form': note_form,
        'status_history': status_history,
        'status_history_count': status_history_count,
        'full_history': full_history,
    }
    return render(request, 'leads/lead/detail.html', context)


@login_required
def lead_edit(request, pk):
    lead = Lead.objects.get(pk=pk)
    old_status = lead.status
    form = LeadForm(instance=lead)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            if old_status != new_status:
                LeadStatusHistory.objects.create(
                    lead=lead,
                    user=request.user,
                    status=new_status,
                )
            form.save()
            return redirect('leads:lead_detail', pk=lead.pk)
    context = {
        'form': form,
        'lead': lead,
    }
    return render(request, 'leads/lead/edit.html', context)


@login_required
def lead_delete(request, pk):
    lead = Lead.objects.get(pk=pk)
    if request.method == 'POST':
        lead.delete()
        return redirect('leads:lead_index')
    return redirect('leads:lead_index')


from ..tasks import scrape_lead_email, scrape_leads_emails_bulk


@login_required
def lead_scrape_email(request, pk):
    lead = Lead.objects.get(pk=pk)
    if request.method == 'POST':
        scrape_lead_email.delay(lead.pk)
    return redirect('leads:lead_detail', pk=lead.pk)


@login_required
def lead_bulk_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_leads')

        if action == 'reject' and selected_ids:
            Lead.objects.filter(pk__in=selected_ids).update(status='rejected')

        if action == 'scrape_emails' and selected_ids:
            scrape_leads_emails_bulk.delay(selected_ids)

    return redirect('leads:lead_index')
