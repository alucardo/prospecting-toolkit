from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from leads.models import CallLog, Pipeline, LeadPipelineStepHistory, LeadPipelineEntry


@login_required
def dashboard(request):
    now = timezone.now()
    today = now.date()
    tomorrow = today + timezone.timedelta(days=1)
    week_start = today - timezone.timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Statystyki kontaktów
    calls_today = CallLog.objects.filter(called_at__date=today, user=request.user).count()
    calls_week = CallLog.objects.filter(called_at__date__gte=week_start, user=request.user).count()
    calls_month = CallLog.objects.filter(called_at__date__gte=month_start, user=request.user).count()

    calls_today_total = CallLog.objects.filter(called_at__date=today).count()
    calls_week_total = CallLog.objects.filter(called_at__date__gte=week_start).count()
    calls_month_total = CallLog.objects.filter(called_at__date__gte=month_start).count()

    effective = Q(status__in=['talked', 'interested', 'not_interested', 'left_contact'])
    effective_today = CallLog.objects.filter(effective, called_at__date=today, user=request.user).count()
    effective_week = CallLog.objects.filter(effective, called_at__date__gte=week_start, user=request.user).count()
    effective_month = CallLog.objects.filter(effective, called_at__date__gte=month_start, user=request.user).count()

    effective_today_total = CallLog.objects.filter(effective, called_at__date=today).count()
    effective_week_total = CallLog.objects.filter(effective, called_at__date__gte=week_start).count()
    effective_month_total = CallLog.objects.filter(effective, called_at__date__gte=month_start).count()

    # Przypomnienia - next_contact_date jest DateTimeField wiec porownujemy z datetime
    tomorrow_end = timezone.make_aware(timezone.datetime.combine(tomorrow, timezone.datetime.max.time()))
    reminders = CallLog.objects.filter(
        is_reminder_active=True,
        next_contact_date__lte=tomorrow_end,
        user=request.user,
    ).select_related('lead', 'lead__city').order_by('next_contact_date')

    # Statystyki pipeline'ów na dashboardzie (ostatnie 30 dni vs poprzednie 30 dni)
    date_30 = now - timezone.timedelta(days=30)
    date_60 = now - timezone.timedelta(days=60)
    pipeline_stats = []
    for pipeline in Pipeline.objects.filter(show_on_dashboard=True).prefetch_related('steps'):
        steps_stats = []
        for step in pipeline.steps.all():
            current_all = LeadPipelineStepHistory.objects.filter(step=step, entered_at__gte=date_30).count()
            current_mine = LeadPipelineStepHistory.objects.filter(step=step, entered_at__gte=date_30, assigned_to=request.user).count()
            prev_all = LeadPipelineStepHistory.objects.filter(step=step, entered_at__gte=date_60, entered_at__lt=date_30).count()
            prev_mine = LeadPipelineStepHistory.objects.filter(step=step, entered_at__gte=date_60, entered_at__lt=date_30, assigned_to=request.user).count()
            steps_stats.append({
                'step': step,
                'current_mine': current_mine,
                'current_all': current_all,
                'prev_mine': prev_mine,
                'prev_all': prev_all,
            })

        # Oblicz procenty względem kroku 1 i względem poprzedniego kroku
        first_all = steps_stats[0]['current_all'] if steps_stats else 0
        first_mine = steps_stats[0]['current_mine'] if steps_stats else 0
        for i, s in enumerate(steps_stats):
            prev_step_all = steps_stats[i - 1]['current_all'] if i > 0 else None
            prev_step_mine = steps_stats[i - 1]['current_mine'] if i > 0 else None
            s['pct_of_first_all'] = round(s['current_all'] / first_all * 100) if first_all else None
            s['pct_of_first_mine'] = round(s['current_mine'] / first_mine * 100) if first_mine else None
            s['pct_of_prev_all'] = round(s['current_all'] / prev_step_all * 100) if (i > 0 and prev_step_all) else None
            s['pct_of_prev_mine'] = round(s['current_mine'] / prev_step_mine * 100) if (i > 0 and prev_step_mine) else None
            s['bar_width'] = s['pct_of_first_all'] if s['pct_of_first_all'] is not None else 0
            # Trend: current vs prev
            s['trend_all'] = s['current_all'] - s['prev_all']
            s['trend_mine'] = s['current_mine'] - s['prev_mine']

        pipeline_stats.append({
            'pipeline': pipeline,
            'steps': steps_stats,
        })

    context = {
        'calls_today': calls_today,
        'calls_week': calls_week,
        'calls_month': calls_month,
        'calls_today_total': calls_today_total,
        'calls_week_total': calls_week_total,
        'calls_month_total': calls_month_total,
        'effective_today': effective_today,
        'effective_week': effective_week,
        'effective_month': effective_month,
        'effective_today_total': effective_today_total,
        'effective_week_total': effective_week_total,
        'effective_month_total': effective_month_total,
        'reminders': reminders,
        'today': today,
        'tomorrow': tomorrow,
        'pipeline_stats': pipeline_stats,
    }
    return render(request, 'leads/dashboard.html', context)
