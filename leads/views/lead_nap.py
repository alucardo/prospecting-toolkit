from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from ..models import Lead, NapDirectory, NapDirectoryTag, LeadNapEntry


@login_required
def lead_nap_index(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')

    # Wszystkie katalogi z informacją czy lead ma już wpis
    tag_filter = request.GET.get('tag', '')
    directories = NapDirectory.objects.prefetch_related('tags').filter(is_active=True)
    if tag_filter:
        directories = directories.filter(tags__id=tag_filter)

    # Słownik: directory_id -> LeadNapEntry
    existing_entries = {
        e.directory_id: e
        for e in LeadNapEntry.objects.filter(lead=lead).select_related('added_by', 'directory')
    }

    rows = []
    for directory in directories:
        rows.append({
            'directory': directory,
            'entry': existing_entries.get(directory.pk),
        })

    tags = NapDirectoryTag.objects.all()

    # Liczniki
    total = len(rows)
    added_by_us = sum(1 for r in rows if r['entry'] and r['entry'].status == LeadNapEntry.STATUS_ADDED_BY_US)
    pre_existing = sum(1 for r in rows if r['entry'] and r['entry'].status == LeadNapEntry.STATUS_PRE_EXISTING)
    pending = total - added_by_us - pre_existing

    return render(request, 'leads/nap/lead_nap_index.html', {
        'lead': lead,
        'rows': rows,
        'tags': tags,
        'tag_filter': tag_filter,
        'stats': {
            'total': total,
            'added_by_us': added_by_us,
            'pre_existing': pre_existing,
            'pending': pending,
        },
    })


@login_required
def lead_nap_set(request, lead_pk, directory_pk):
    """Tworzy lub aktualizuje wpis NAP dla klienta. POST only."""
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    directory = get_object_or_404(NapDirectory, pk=directory_pk)

    if request.method == 'POST':
        status = request.POST.get('status', '')
        notes = request.POST.get('notes', '').strip()

        if status in (LeadNapEntry.STATUS_ADDED_BY_US, LeadNapEntry.STATUS_PRE_EXISTING):
            entry, _ = LeadNapEntry.objects.update_or_create(
                lead=lead,
                directory=directory,
                defaults={
                    'status': status,
                    'notes': notes,
                    'added_by': request.user,
                },
            )
        elif status == 'remove':
            LeadNapEntry.objects.filter(lead=lead, directory=directory).delete()

    tag_filter = request.GET.get('tag', '')
    redirect_url = f"{request.path.rsplit('/set', 1)[0].rsplit('/', 2)[0]}/"
    next_url = request.POST.get('next') or f"/klienci/{lead_pk}/nap/"
    return redirect(next_url + (f"?tag={tag_filter}" if tag_filter else ""))
