from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import PostIdeaCategory, PostIdea


@login_required
def idea_index(request):
    """Lista wszystkich kategorii i pomysłów."""
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_category':
            name = request.POST.get('name', '').strip()
            if name:
                PostIdeaCategory.objects.get_or_create(name=name)

        elif action == 'edit_category':
            pk = request.POST.get('pk')
            name = request.POST.get('name', '').strip()
            if name:
                PostIdeaCategory.objects.filter(pk=pk).update(name=name)

        elif action == 'delete_category':
            pk = request.POST.get('pk')
            PostIdeaCategory.objects.filter(pk=pk).delete()

        elif action == 'add_idea':
            cat_pk = request.POST.get('category_pk')
            title = request.POST.get('title', '').strip()
            hint = request.POST.get('hint', '').strip()
            if cat_pk and title:
                cat = get_object_or_404(PostIdeaCategory, pk=cat_pk)
                PostIdea.objects.create(category=cat, title=title, hint=hint)

        elif action == 'edit_idea':
            pk = request.POST.get('pk')
            title = request.POST.get('title', '').strip()
            hint = request.POST.get('hint', '').strip()
            if title:
                PostIdea.objects.filter(pk=pk).update(title=title, hint=hint)

        elif action == 'delete_idea':
            pk = request.POST.get('pk')
            PostIdea.objects.filter(pk=pk).delete()

        return redirect('leads:idea_index')

    categories = PostIdeaCategory.objects.prefetch_related('ideas').all()
    return render(request, 'leads/post_ideas/index.html', {
        'categories': categories,
    })
