from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from leads.models import CallLog


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

    effective = Q(status__in=['talked', 'interested', 'not_interested'])
    effective_today = CallLog.objects.filter(effective, called_at__date=today, user=request.user).count()
    effective_week = CallLog.objects.filter(effective, called_at__date__gte=week_start, user=request.user).count()
    effective_month = CallLog.objects.filter(effective, called_at__date__gte=month_start, user=request.user).count()

    # Przypomnienia
    reminders = CallLog.objects.filter(
        is_reminder_active=True,
        next_contact_date__lte=tomorrow,
        user=request.user,
    ).select_related('lead', 'lead__city').order_by('next_contact_date')

    context = {
        'calls_today': calls_today,
        'calls_week': calls_week,
        'calls_month': calls_month,
        'effective_today': effective_today,
        'effective_week': effective_week,
        'effective_month': effective_month,
        'reminders': reminders,
        'today': today,
        'tomorrow': tomorrow,
    }
    return render(request, 'leads/dashboard.html', context)
