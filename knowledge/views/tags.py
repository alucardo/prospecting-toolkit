from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import KnowledgeTag


@login_required
def tag_index(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            if name:
                KnowledgeTag.objects.get_or_create(name=name)

        elif action == 'edit':
            pk = request.POST.get('pk')
            name = request.POST.get('name', '').strip()
            if name:
                KnowledgeTag.objects.filter(pk=pk).update(name=name)

        elif action == 'delete':
            pk = request.POST.get('pk')
            KnowledgeTag.objects.filter(pk=pk).delete()

        return redirect('knowledge:tag_index')

    tags = KnowledgeTag.objects.annotate(
        video_count=__import__('django.db.models', fromlist=['Count']).Count('videos')
    )
    return render(request, 'knowledge/tags/index.html', {'tags': tags})
