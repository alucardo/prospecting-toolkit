from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Lead, LeadTask


@login_required
def all_tasks_index(request):
    """Wszystkie nieukończone zadania wszystkich klientów."""
    tasks = (
        LeadTask.objects
        .filter(is_done=False, lead__status='client')
        .select_related('lead', 'lead__city')
        .order_by('lead__name', '-created_at')
    )

    if request.method == 'POST':
        task_pk = request.POST.get('task_pk')
        action = request.POST.get('action')
        task = get_object_or_404(LeadTask, pk=task_pk, lead__status='client')

        if action == 'toggle':
            task.is_done = True
            task.done_at = timezone.now()
            task.save(update_fields=['is_done', 'done_at'])

        elif action == 'delete':
            task.delete()

        return redirect('leads:all_tasks_index')

    # Grupowanie po kliencie
    grouped = {}
    for task in tasks:
        lead = task.lead
        if lead.pk not in grouped:
            grouped[lead.pk] = {'lead': lead, 'tasks': []}
        grouped[lead.pk]['tasks'].append(task)

    return render(request, 'leads/tasks/all_tasks.html', {
        'grouped': grouped.values(),
        'total_count': tasks.count(),
    })
