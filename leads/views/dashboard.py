from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from leads.models import CallLog

def dashboard(request):
    now = timezone.now()
    today = now.date()
    week_start = today - timezone.timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Wszystkie kontakty
    calls_today = CallLog.objects.filter(called_at__date=today).count()
    calls_week = CallLog.objects.filter(called_at__date__gte=week_start).count()
    calls_month = CallLog.objects.filter(called_at__date__gte=month_start).count()

    # Skuteczne kontakty (bez nie odebrano i zadzwonić później)
    effective = Q(status__in=['talked', 'interested', 'not_interested'])
    effective_today = CallLog.objects.filter(effective, called_at__date=today).count()
    effective_week = CallLog.objects.filter(effective, called_at__date__gte=week_start).count()
    effective_month = CallLog.objects.filter(effective, called_at__date__gte=month_start).count()

    context = {
        'calls_today': calls_today,
        'calls_week': calls_week,
        'calls_month': calls_month,
        'effective_today': effective_today,
        'effective_week': effective_week,
        'effective_month': effective_month,
    }
    return render(request, 'leads/dashboard.html', context)