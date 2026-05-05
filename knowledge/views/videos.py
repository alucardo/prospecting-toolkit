from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import VideoInspiration, KnowledgeTag, KnowledgeSettings


@login_required
def video_index(request):
    videos = VideoInspiration.objects.prefetch_related('tags', 'created_by')

    tag_filter = request.GET.getlist('tag')
    if tag_filter:
        for t in tag_filter:
            videos = videos.filter(tags__pk=t)
        videos = videos.distinct()

    search = request.GET.get('search', '').strip()
    if search:
        videos = videos.filter(title__icontains=search)

    tags = KnowledgeTag.objects.all()

    return render(request, 'knowledge/video/index.html', {
        'videos': videos,
        'tags': tags,
        'tag_filter': [int(t) for t in tag_filter if t.isdigit()],
        'search': search,
    })


@login_required
def video_create(request):
    tags = KnowledgeTag.objects.all()
    settings = KnowledgeSettings.get()

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        drive_url = request.POST.get('drive_url', '').strip()
        description = request.POST.get('description', '').strip()
        tag_ids = request.POST.getlist('tags')

        if title and drive_url:
            video = VideoInspiration.objects.create(
                title=title,
                drive_url=drive_url,
                description=description,
                created_by=request.user,
            )
            video.tags.set(tag_ids)
            return redirect('knowledge:video_index')

    return render(request, 'knowledge/video/form.html', {
        'tags': tags,
        'video': None,
        'settings': settings,
    })


@login_required
def video_edit(request, pk):
    video = get_object_or_404(VideoInspiration, pk=pk)
    tags = KnowledgeTag.objects.all()
    settings = KnowledgeSettings.get()

    if request.method == 'POST':
        video.title = request.POST.get('title', '').strip()
        video.drive_url = request.POST.get('drive_url', '').strip()
        video.description = request.POST.get('description', '').strip()
        video.save()
        video.tags.set(request.POST.getlist('tags'))
        return redirect('knowledge:video_index')

    return render(request, 'knowledge/video/form.html', {
        'tags': tags,
        'video': video,
        'settings': settings,
    })


@login_required
def video_delete(request, pk):
    video = get_object_or_404(VideoInspiration, pk=pk)
    if request.method == 'POST':
        video.delete()
    return redirect('knowledge:video_index')


@login_required
def knowledge_settings(request):
    settings = KnowledgeSettings.get()

    if request.method == 'POST':
        settings.video_folder_url = request.POST.get('video_folder_url', '').strip()
        settings.tiktok_downloader_url = request.POST.get('tiktok_downloader_url', '').strip()
        settings.instagram_downloader_url = request.POST.get('instagram_downloader_url', '').strip()
        settings.save()
        return redirect('knowledge:settings')

    return render(request, 'knowledge/settings.html', {'settings': settings})
