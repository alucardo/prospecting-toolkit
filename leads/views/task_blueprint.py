from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import TaskBlueprint, TaskBlueprintItem


@login_required
def blueprint_index(request):
    blueprints = TaskBlueprint.objects.prefetch_related('items').all()
    return render(request, 'leads/tasks/blueprint_index.html', {
        'blueprints': blueprints,
    })


@login_required
def blueprint_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            blueprint = TaskBlueprint.objects.create(name=name, description=description)
            return redirect('leads:blueprint_detail', pk=blueprint.pk)
    return render(request, 'leads/tasks/blueprint_form.html', {'blueprint': None})


@login_required
def blueprint_detail(request, pk):
    blueprint = get_object_or_404(TaskBlueprint, pk=pk)
    items = blueprint.items.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_item':
            title = request.POST.get('title', '').strip()
            if title:
                max_order = items.last().order + 1 if items.exists() else 0
                TaskBlueprintItem.objects.create(
                    blueprint=blueprint, title=title, order=max_order
                )

        elif action == 'delete_item':
            item_pk = request.POST.get('item_pk')
            TaskBlueprintItem.objects.filter(pk=item_pk, blueprint=blueprint).delete()

        elif action == 'edit_item':
            item_pk = request.POST.get('item_pk')
            title = request.POST.get('title', '').strip()
            if title:
                TaskBlueprintItem.objects.filter(pk=item_pk, blueprint=blueprint).update(title=title)

        elif action == 'move_up':
            item_pk = request.POST.get('item_pk')
            item = get_object_or_404(TaskBlueprintItem, pk=item_pk, blueprint=blueprint)
            prev = items.filter(order__lt=item.order).last()
            if prev:
                item.order, prev.order = prev.order, item.order
                item.save(update_fields=['order'])
                prev.save(update_fields=['order'])

        elif action == 'move_down':
            item_pk = request.POST.get('item_pk')
            item = get_object_or_404(TaskBlueprintItem, pk=item_pk, blueprint=blueprint)
            next_item = items.filter(order__gt=item.order).first()
            if next_item:
                item.order, next_item.order = next_item.order, item.order
                item.save(update_fields=['order'])
                next_item.save(update_fields=['order'])

        return redirect('leads:blueprint_detail', pk=blueprint.pk)

    return render(request, 'leads/tasks/blueprint_detail.html', {
        'blueprint': blueprint,
        'items': items,
    })


@login_required
def blueprint_edit(request, pk):
    blueprint = get_object_or_404(TaskBlueprint, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            blueprint.name = name
            blueprint.description = description
            blueprint.save()
        return redirect('leads:blueprint_detail', pk=blueprint.pk)
    return render(request, 'leads/tasks/blueprint_form.html', {'blueprint': blueprint})


@login_required
def blueprint_delete(request, pk):
    blueprint = get_object_or_404(TaskBlueprint, pk=pk)
    if request.method == 'POST':
        blueprint.delete()
    return redirect('leads:blueprint_index')
