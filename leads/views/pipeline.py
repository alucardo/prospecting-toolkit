from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from ..models import Pipeline, PipelineStep, LeadPipelineEntry, LeadPipelineStepHistory, Lead
from ..forms import PipelineForm, PipelineStepForm, LeadPipelineEntryForm


@login_required
def pipeline_index(request):
    pipelines = Pipeline.objects.annotate(
        entries_count=Count('entries')
    )
    return render(request, 'leads/pipeline/index.html', {'pipelines': pipelines})


@login_required
def pipeline_create(request):
    form = PipelineForm()
    if request.method == 'POST':
        form = PipelineForm(request.POST)
        if form.is_valid():
            pipeline = form.save()
            return redirect('leads:pipeline_detail', pk=pipeline.pk)
    return render(request, 'leads/pipeline/form.html', {'form': form, 'title': 'Nowy pipeline'})


@login_required
def pipeline_edit(request, pk):
    pipeline = get_object_or_404(Pipeline, pk=pk)
    form = PipelineForm(instance=pipeline)
    if request.method == 'POST':
        form = PipelineForm(request.POST, instance=pipeline)
        if form.is_valid():
            form.save()
            return redirect('leads:pipeline_detail', pk=pipeline.pk)
    return render(request, 'leads/pipeline/form.html', {'form': form, 'title': 'Edytuj pipeline', 'pipeline': pipeline})


@login_required
def pipeline_detail(request, pk):
    pipeline = get_object_or_404(Pipeline, pk=pk)
    steps = pipeline.steps.all()

    # Filtry okresu
    period = request.GET.get('period', 'month')
    now = timezone.now()
    if period == 'week':
        date_from = now - timezone.timedelta(weeks=1)
    elif period == 'month':
        date_from = now - timezone.timedelta(days=30)
    elif period == 'quarter':
        date_from = now - timezone.timedelta(days=90)
    else:
        date_from = None

    # Statystyki per krok
    stats = []
    period_length = (now - date_from) if date_from else None
    date_prev = (date_from - period_length) if period_length else None

    for step in steps:
        current_qs = LeadPipelineStepHistory.objects.filter(step=step)
        current_mine = current_qs.filter(assigned_to=request.user)
        if date_from:
            current_qs = current_qs.filter(entered_at__gte=date_from)
            current_mine = current_mine.filter(entered_at__gte=date_from)

        prev_qs = LeadPipelineStepHistory.objects.filter(step=step)
        prev_mine = prev_qs.filter(assigned_to=request.user)
        if date_from and date_prev:
            prev_qs = prev_qs.filter(entered_at__gte=date_prev, entered_at__lt=date_from)
            prev_mine = prev_mine.filter(entered_at__gte=date_prev, entered_at__lt=date_from)
        else:
            prev_qs = prev_qs.none()
            prev_mine = prev_mine.none()

        stats.append({
            'step': step,
            'current_all': current_qs.count(),
            'current_mine': current_mine.count(),
            'prev_all': prev_qs.count(),
            'prev_mine': prev_mine.count(),
        })

    # Oblicz procenty
    first_all = stats[0]['current_all'] if stats else 0
    first_mine = stats[0]['current_mine'] if stats else 0
    for i, s in enumerate(stats):
        prev_step_all = stats[i - 1]['current_all'] if i > 0 else None
        prev_step_mine = stats[i - 1]['current_mine'] if i > 0 else None
        s['pct_of_first_all'] = round(s['current_all'] / first_all * 100) if first_all else None
        s['pct_of_first_mine'] = round(s['current_mine'] / first_mine * 100) if first_mine else None
        s['pct_of_prev_all'] = round(s['current_all'] / prev_step_all * 100) if (i > 0 and prev_step_all) else None
        s['pct_of_prev_mine'] = round(s['current_mine'] / prev_step_mine * 100) if (i > 0 and prev_step_mine) else None
        s['bar_width_all'] = s['pct_of_first_all'] if s['pct_of_first_all'] is not None else 0
        s['bar_width_mine'] = s['pct_of_first_mine'] if s['pct_of_first_mine'] is not None else 0
        s['trend_all'] = s['current_all'] - s['prev_all']
        s['trend_mine'] = s['current_mine'] - s['prev_mine']

    return render(request, 'leads/pipeline/detail.html', {
        'pipeline': pipeline,
        'steps': steps,
        'stats': stats,
        'period': period,
    })


@login_required
def pipeline_step_create(request, pipeline_pk):
    pipeline = get_object_or_404(Pipeline, pk=pipeline_pk)
    # Ustaw domyślny order jako następny
    next_order = (pipeline.steps.order_by('-order').values_list('order', flat=True).first() or 0) + 1
    form = PipelineStepForm(initial={'order': next_order})
    if request.method == 'POST':
        form = PipelineStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.pipeline = pipeline
            step.save()
            return redirect('leads:pipeline_detail', pk=pipeline.pk)
    return render(request, 'leads/pipeline/step_form.html', {'form': form, 'pipeline': pipeline, 'title': 'Nowy krok'})


@login_required
def pipeline_step_edit(request, pipeline_pk, step_pk):
    pipeline = get_object_or_404(Pipeline, pk=pipeline_pk)
    step = get_object_or_404(PipelineStep, pk=step_pk, pipeline=pipeline)
    form = PipelineStepForm(instance=step)
    if request.method == 'POST':
        form = PipelineStepForm(request.POST, instance=step)
        if form.is_valid():
            form.save()
            return redirect('leads:pipeline_detail', pk=pipeline.pk)
    return render(request, 'leads/pipeline/step_form.html', {'form': form, 'pipeline': pipeline, 'title': 'Edytuj krok'})


@login_required
def pipeline_step_delete(request, pipeline_pk, step_pk):
    pipeline = get_object_or_404(Pipeline, pk=pipeline_pk)
    step = get_object_or_404(PipelineStep, pk=step_pk, pipeline=pipeline)
    if request.method == 'POST':
        step.delete()
    return redirect('leads:pipeline_detail', pk=pipeline.pk)


@login_required
def lead_pipeline_add(request, lead_pk):
    """Dodaj leada do pipeline'u."""
    lead = get_object_or_404(Lead, pk=lead_pk)

    # Sprawdź czy lead nie jest już w pipeline
    if hasattr(lead, 'pipeline_entry'):
        return redirect('leads:lead_detail', pk=lead.pk)

    pipeline_id = request.POST.get('pipeline') or request.GET.get('pipeline')
    if pipeline_id:
        pipeline = get_object_or_404(Pipeline, pk=pipeline_id)
    else:
        # Użyj domyślnego pipeline jeśli istnieje
        pipeline = Pipeline.objects.filter(is_default=True).first()

    # Pierwszy krok domyślnego pipeline
    default_step = pipeline.steps.order_by('order').first() if pipeline else None

    form = LeadPipelineEntryForm(
        pipeline=pipeline,
        user=request.user,
        initial={'pipeline': pipeline, 'current_step': default_step} if pipeline else {},
    )
    pipelines = Pipeline.objects.all()

    if request.method == 'POST':
        form = LeadPipelineEntryForm(request.POST, pipeline=pipeline, user=request.user)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.lead = lead
            entry.save()
            # Zapisz historię pierwszego kroku
            LeadPipelineStepHistory.objects.create(
                entry=entry,
                step=entry.current_step,
                assigned_to=entry.assigned_to,
            )
            return redirect('leads:lead_detail', pk=lead.pk)

    return render(request, 'leads/pipeline/lead_add.html', {
        'lead': lead,
        'form': form,
        'pipelines': pipelines,
        'selected_pipeline': pipeline,
    })


@login_required
def lead_pipeline_move(request, lead_pk):
    """Przesuń leada do wybranego kroku, automatycznie przechodząc przez kroki pośrednie."""
    lead = get_object_or_404(Lead, pk=lead_pk)
    entry = get_object_or_404(LeadPipelineEntry, lead=lead)

    if request.method == 'POST':
        step_pk = request.POST.get('step')
        target_step = get_object_or_404(PipelineStep, pk=step_pk, pipeline=entry.pipeline)
        current_order = entry.current_step.order
        target_order = target_step.order

        # Pobierz kroki pośrednie (i docelowy) posortowane po order
        if target_order > current_order:
            # Przesunięcie do przodu — dodaj wszystkie kroki między obecnym a docelowym
            steps_to_record = entry.pipeline.steps.filter(
                order__gt=current_order,
                order__lte=target_order,
            ).order_by('order')
        elif target_order < current_order:
            # Cofnięcie — tylko sam krok docelowy (bez pośrednich)
            steps_to_record = entry.pipeline.steps.filter(pk=target_step.pk)
        else:
            steps_to_record = []

        # Pobierz zestaw kroków już zapisanych w historii (unikamy duplikatów)
        already_recorded = set(
            entry.step_history.values_list('step_id', flat=True)
        )

        for step in steps_to_record:
            if step.pk not in already_recorded:
                LeadPipelineStepHistory.objects.create(
                    entry=entry,
                    step=step,
                    assigned_to=entry.assigned_to,
                )

        entry.current_step = target_step
        entry.save(update_fields=['current_step'])

    return redirect('leads:lead_detail', pk=lead.pk)


@login_required
def lead_pipeline_edit(request, lead_pk):
    """Edytuj przypisanie (handlowiec)."""
    lead = get_object_or_404(Lead, pk=lead_pk)
    entry = get_object_or_404(LeadPipelineEntry, lead=lead)

    form = LeadPipelineEntryForm(instance=entry, pipeline=entry.pipeline)
    if request.method == 'POST':
        form = LeadPipelineEntryForm(request.POST, instance=entry, pipeline=entry.pipeline)
        if form.is_valid():
            form.save()
            return redirect('leads:lead_detail', pk=lead.pk)

    return render(request, 'leads/pipeline/lead_edit.html', {'lead': lead, 'entry': entry, 'form': form})


@login_required
def pipeline_steps_json(request, pipeline_pk):
    """JSON dla dynamicznego ładowania kroków po wyborze pipeline."""
    pipeline = get_object_or_404(Pipeline, pk=pipeline_pk)
    steps = list(pipeline.steps.values('pk', 'name', 'order'))
    return JsonResponse({'steps': steps})
