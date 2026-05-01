from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import Lead, ContentPost, ContentPostVersion


@login_required
def content_version_preview(request, lead_pk, post_pk, version_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    post = get_object_or_404(ContentPost, pk=post_pk, lead=lead)
    version = get_object_or_404(ContentPostVersion, pk=version_pk, post=post)

    return render(request, 'leads/content/version_preview.html', {
        'lead': lead,
        'post': post,
        'version': version,
    })


@login_required
def content_index(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    posts = lead.content_posts.prefetch_related('versions').all()

    for post in posts:
        post.current_ver = post.versions.filter(is_current=True).first()

    return render(request, 'leads/content/index.html', {
        'lead': lead,
        'posts': posts,
        'status_choices': ContentPost.STATUS_CHOICES,
    })


@login_required
def content_create(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')

    if request.method == 'POST':
        post = ContentPost.objects.create(
            lead=lead,
            channel=request.POST.get('channel', ContentPost.CHANNEL_GBP),
            post_type=request.POST.get('post_type', ContentPost.TYPE_NEWS),
            status=request.POST.get('status', ContentPost.STATUS_DRAFT),
            published_at=request.POST.get('published_at') or None,
        )
        ContentPostVersion.objects.create(
            post=post,
            version_number=1,
            title=request.POST.get('title', '').strip(),
            body=request.POST.get('body', '').strip(),
            drive_url=request.POST.get('drive_url', '').strip(),
            cta_text=request.POST.get('cta_text', '').strip(),
            cta_url=request.POST.get('cta_url', '').strip(),
            notes=request.POST.get('notes', '').strip(),
            is_current=True,
            created_by=request.user,
        )
        return redirect('leads:content_detail', lead_pk=lead.pk, post_pk=post.pk)

    return render(request, 'leads/content/form.html', {
        'lead': lead,
        'post': None,
        'version': None,
        'status_choices': ContentPost.STATUS_CHOICES,
        'channel_choices': ContentPost.CHANNEL_CHOICES,
        'type_choices': ContentPost.TYPE_CHOICES,
    })


@login_required
def content_detail(request, lead_pk, post_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    post = get_object_or_404(ContentPost, pk=post_pk, lead=lead)
    current = post.versions.filter(is_current=True).first()
    history = post.versions.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_status':
            post.status = request.POST.get('status', post.status)
            post.published_at = request.POST.get('published_at') or None
            post.save(update_fields=['status', 'published_at', 'updated_at'])

        elif action == 'save_current' and current:
            current.title = request.POST.get('title', '').strip()
            current.body = request.POST.get('body', '').strip()
            current.drive_url = request.POST.get('drive_url', '').strip()
            current.cta_text = request.POST.get('cta_text', '').strip()
            current.cta_url = request.POST.get('cta_url', '').strip()
            current.notes = request.POST.get('notes', '').strip()
            current.save()

        elif action == 'save_new':
            post.versions.filter(is_current=True).update(is_current=False)
            last = post.versions.order_by('-version_number').first()
            next_num = (last.version_number + 1) if last else 1
            ContentPostVersion.objects.create(
                post=post,
                version_number=next_num,
                title=request.POST.get('title', '').strip(),
                body=request.POST.get('body', '').strip(),
                drive_url=request.POST.get('drive_url', '').strip(),
                cta_text=request.POST.get('cta_text', '').strip(),
                cta_url=request.POST.get('cta_url', '').strip(),
                notes=request.POST.get('notes', '').strip(),
                is_current=True,
                created_by=request.user,
            )
            post.save(update_fields=['updated_at'])

        elif action == 'delete':
            post.delete()
            return redirect('leads:content_index', lead_pk=lead.pk)

        return redirect('leads:content_detail', lead_pk=lead.pk, post_pk=post.pk)

    return render(request, 'leads/content/detail.html', {
        'lead': lead,
        'post': post,
        'current': current,
        'history': history,
        'status_choices': ContentPost.STATUS_CHOICES,
    })
