from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Lead, LeadTask, TaskBlueprint


@login_required
def lead_task_index(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    tasks = lead.tasks.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            title = request.POST.get('title', '').strip()
            due_start = request.POST.get('due_date_start') or None
            due_end = request.POST.get('due_date_end') or None
            if title:
                LeadTask.objects.create(
                    lead=lead, title=title,
                    due_date_start=due_start,
                    due_date_end=due_end,
                )

        elif action == 'toggle':
            task_pk = request.POST.get('task_pk')
            task = get_object_or_404(LeadTask, pk=task_pk, lead=lead)
            task.is_done = not task.is_done
            task.done_at = timezone.now() if task.is_done else None
            task.save(update_fields=['is_done', 'done_at'])

        elif action == 'delete':
            task_pk = request.POST.get('task_pk')
            task = get_object_or_404(LeadTask, pk=task_pk, lead=lead)
            task.delete()

        elif action == 'edit':
            task_pk = request.POST.get('task_pk')
            title = request.POST.get('title', '').strip()
            due_start = request.POST.get('due_date_start') or None
            due_end = request.POST.get('due_date_end') or None
            task = get_object_or_404(LeadTask, pk=task_pk, lead=lead)
            if title:
                task.title = title
                task.due_date_start = due_start
                task.due_date_end = due_end
                task.save(update_fields=['title', 'due_date_start', 'due_date_end'])

        return redirect('leads:lead_task_index', lead_pk=lead.pk)

    pending = tasks.filter(is_done=False)
    done = tasks.filter(is_done=True)
    blueprints = TaskBlueprint.objects.prefetch_related('items').all()

    return render(request, 'leads/tasks/index.html', {
        'lead': lead,
        'pending': pending,
        'done': done,
        'pending_count': pending.count(),
        'done_count': done.count(),
        'blueprints': blueprints,
    })


@login_required
def apply_blueprint(request, lead_pk, blueprint_pk):
    """Kopiuje zadania z blueprintu do klienta. POST only."""
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    blueprint = get_object_or_404(TaskBlueprint, pk=blueprint_pk)

    if request.method == 'POST':
        items = blueprint.items.order_by('order', 'id')
        for item in items:
            LeadTask.objects.create(lead=lead, title=item.title)

    return redirect('leads:lead_task_index', lead_pk=lead.pk)


@login_required
def all_tasks_index(request):
    """Wszystkie nieukończone zadania wszystkich klientów."""
    today = timezone.now().date()

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

    # Liczniki do boxów
    overdue_count = 0
    active_count = 0
    for task in tasks:
        status = task.due_status
        if status == 'overdue':
            overdue_count += 1
        elif status == 'active':
            active_count += 1

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
        'overdue_count': overdue_count,
        'active_count': active_count,
        'today': today,
    })
