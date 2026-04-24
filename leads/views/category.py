from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count
from ..models import LeadCategory, Lead


@login_required
def category_index(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            color = request.POST.get('color', '#6366f1')
            if name:
                LeadCategory.objects.get_or_create(name=name, defaults={'color': color})

        elif action == 'edit':
            pk = request.POST.get('pk')
            name = request.POST.get('name', '').strip()
            color = request.POST.get('color', '#6366f1')
            if name:
                LeadCategory.objects.filter(pk=pk).update(name=name, color=color)

        elif action == 'delete':
            pk = request.POST.get('pk')
            LeadCategory.objects.filter(pk=pk).delete()

        return redirect('leads:category_index')

    categories = LeadCategory.objects.annotate(lead_count=Count('leads'))
    return render(request, 'leads/category/index.html', {'categories': categories})


@login_required
def lead_category_set(request, lead_pk):
    """AJAX — ustawia kategorie dla leada (toggle)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    lead = get_object_or_404(Lead, pk=lead_pk)
    category_pk = request.POST.get('category_pk')
    category = get_object_or_404(LeadCategory, pk=category_pk)

    if lead.categories.filter(pk=category_pk).exists():
        lead.categories.remove(category)
        added = False
    else:
        lead.categories.add(category)
        added = True

    return JsonResponse({'ok': True, 'added': added, 'category_pk': category_pk})
