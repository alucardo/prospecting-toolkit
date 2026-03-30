import calendar
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Lead, GBPMetricsSnapshot


@login_required
def gbp_metrics_index(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    now = timezone.now()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            year = int(request.POST.get('year', now.year))
            month = int(request.POST.get('month', now.month))
            calls = request.POST.get('calls') or None
            profile_views = request.POST.get('profile_views') or None
            direction_requests = request.POST.get('direction_requests') or None
            website_visits = request.POST.get('website_visits') or None

            GBPMetricsSnapshot.objects.update_or_create(
                lead=lead,
                year=year,
                month=month,
                day=None,
                source=GBPMetricsSnapshot.SOURCE_MANUAL,
                defaults={
                    'calls': calls,
                    'profile_views': profile_views,
                    'direction_requests': direction_requests,
                    'website_visits': website_visits,
                },
            )

        elif action == 'delete':
            pk = request.POST.get('pk')
            GBPMetricsSnapshot.objects.filter(pk=pk, lead=lead).delete()

        return redirect('leads:gbp_metrics_index', lead_pk=lead.pk)

    # Tylko ręczne wpisy miesięczne (day=NULL) — dzienne pojawią się z API
    snapshots = lead.gbp_metrics.filter(day__isnull=True, source=GBPMetricsSnapshot.SOURCE_MANUAL)

    # Miesiące do selecta — bieżący rok i rok poprzedni
    months = [(y, m) for y in [now.year, now.year - 1] for m in range(1, 13)]
    months_choices = [
        (y, m, f"{calendar.month_name[m]} {y}")
        for y, m in months
    ]

    return render(request, 'leads/gbp_metrics/index.html', {
        'lead': lead,
        'snapshots': snapshots,
        'months_choices': months_choices,
        'current_year': now.year,
        'current_month': now.month,
    })
