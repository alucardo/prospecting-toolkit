from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from ..models import NapDirectory, NapDirectoryTag


# ---------------------------------------------------------------------------
# Katalogi NAP
# ---------------------------------------------------------------------------

@login_required
def nap_directory_index(request):
    tag_filter = request.GET.get('tag', '')
    search = request.GET.get('search', '').strip()

    directories = NapDirectory.objects.prefetch_related('tags').annotate(
        tag_count=Count('tags', distinct=True)
    )

    if tag_filter:
        directories = directories.filter(tags__id=tag_filter)

    if search:
        directories = directories.filter(name__icontains=search)

    tags = NapDirectoryTag.objects.annotate(dir_count=Count('directories'))

    return render(request, 'leads/nap/directory_index.html', {
        'directories': directories,
        'tags': tags,
        'tag_filter': tag_filter,
        'search': search,
    })


@login_required
def nap_directory_create(request):
    tags = NapDirectoryTag.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        url = request.POST.get('url', '').strip()
        notes = request.POST.get('notes', '').strip()
        is_active = 'is_active' in request.POST
        selected_tags = request.POST.getlist('tags')

        if name and url:
            directory = NapDirectory.objects.create(
                name=name, url=url, notes=notes, is_active=is_active
            )
            directory.tags.set(selected_tags)
        return redirect('leads:nap_directory_index')

    return render(request, 'leads/nap/directory_form.html', {
        'directory': None,
        'tags': tags,
    })


@login_required
def nap_directory_edit(request, pk):
    directory = get_object_or_404(NapDirectory, pk=pk)
    tags = NapDirectoryTag.objects.all()

    if request.method == 'POST':
        directory.name = request.POST.get('name', '').strip()
        directory.url = request.POST.get('url', '').strip()
        directory.notes = request.POST.get('notes', '').strip()
        directory.is_active = 'is_active' in request.POST
        directory.save()
        directory.tags.set(request.POST.getlist('tags'))
        return redirect('leads:nap_directory_index')

    return render(request, 'leads/nap/directory_form.html', {
        'directory': directory,
        'tags': tags,
        'selected_tags': list(directory.tags.values_list('id', flat=True)),
    })


@login_required
def nap_directory_delete(request, pk):
    directory = get_object_or_404(NapDirectory, pk=pk)
    if request.method == 'POST':
        directory.delete()
    return redirect('leads:nap_directory_index')


# ---------------------------------------------------------------------------
# Tagi NAP
# ---------------------------------------------------------------------------

@login_required
def nap_tag_index(request):
    tags = NapDirectoryTag.objects.annotate(dir_count=Count('directories'))
    return render(request, 'leads/nap/tag_index.html', {'tags': tags})


@login_required
def nap_tag_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            NapDirectoryTag.objects.get_or_create(name=name)
        return redirect('leads:nap_tag_index')
    return render(request, 'leads/nap/tag_form.html', {'tag': None})


@login_required
def nap_tag_edit(request, pk):
    tag = get_object_or_404(NapDirectoryTag, pk=pk)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            tag.name = name
            tag.save()
        return redirect('leads:nap_tag_index')
    return render(request, 'leads/nap/tag_form.html', {'tag': tag})


@login_required
def nap_tag_delete(request, pk):
    tag = get_object_or_404(NapDirectoryTag, pk=pk)
    if request.method == 'POST':
        tag.delete()
    return redirect('leads:nap_tag_index')
