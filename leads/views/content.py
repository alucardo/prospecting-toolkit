from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from ..models import Lead, ContentPost, ContentPostVersion, PostIdeaCategory
import json


@login_required
def content_generate_ai(request, lead_pk):
    """AJAX — generuje treść posta przez OpenAI."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Błąd parsowania danych'}, status=400)

    lead = get_object_or_404(Lead, pk=lead_pk, status='client')

    # Pobierz brief marki
    from ..models import BrandProfile
    try:
        brand = lead.brand_profile
    except BrandProfile.DoesNotExist:
        brand = None

    # Historia konwersacji z frontendu
    messages = data.get('messages', [])
    user_input = data.get('user_input', '').strip()
    idea_title = data.get('idea_title', '').strip()
    idea_hint = data.get('idea_hint', '').strip()
    channel = data.get('channel', 'Wizytówka Google')
    post_type = data.get('post_type', 'Aktualność')

    if not user_input and not idea_title:
        return JsonResponse({'error': 'Podaj temat lub wybierz pomysł'}, status=400)

    # Buduj system prompt z briefu marki
    system_parts = [
        f'Jesteś ekspertem od marketingu lokalnego. Piszesz posty dla firmy "{lead.name}".',
        f'Kanal: {channel}. Typ posta: {post_type}.',
        'Maksymalna długość treści posta: 1500 znaków.',
        'Zwracaj TYLKO treść posta — bez tytułu, bez komentarzy, bez cudzysłowów otaczających treść.',
    ]

    if brand:
        if brand.archetype:
            system_parts.append(f'Archetyp marki: {brand.get_archetype_display()}.')
        if brand.tone_of_voice:
            system_parts.append(f'Ton komunikacji: {brand.tone_of_voice}')
        if brand.target_audience:
            system_parts.append(f'Grupa docelowa: {brand.target_audience}')
        if brand.language_rules:
            system_parts.append(f'Zasady językowe: {brand.language_rules}')
        if brand.avoid:
            system_parts.append(f'Czego bezwzględnie unikaj: {brand.avoid}')
        if brand.keywords:
            system_parts.append(f'Słowa kluczowe marki: {brand.keywords}')
        if brand.usp:
            system_parts.append(f'Unikalna propozycja wartości: {brand.usp}')

    system_prompt = ' '.join(system_parts)

    # Pierwsze wywołanie — buduj wiadomość użytkownika
    if not messages:
        user_msg_parts = []
        if idea_title:
            user_msg_parts.append(f'Temat posta: {idea_title}')
            if idea_hint:
                user_msg_parts.append(f'Wskazówka: {idea_hint}')
        if user_input:
            user_msg_parts.append(f'Dodatkowe informacje / uwagi: {user_input}')
        user_message = '\n'.join(user_msg_parts)
    else:
        # Kolejne wywołanie — uwagi do poprawki
        user_message = f'Popraw post zgodnie z uwagami: {user_input}'

    # Dodaj nową wiadomość do historii
    messages.append({'role': 'user', 'content': user_message})

    # Wywołaj OpenAI przez requests
    from ..models import AppSettings
    import requests as req

    api_key = AppSettings.get().openai_api_key
    if not api_key:
        return JsonResponse({'error': 'Brak klucza OpenAI w Ustawieniach aplikacji'}, status=500)

    try:
        resp = req.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'gpt-4.1',
                'messages': [{'role': 'system', 'content': system_prompt}] + messages,
                'max_tokens': 600,
                'temperature': 0.75,
            },
            timeout=30,
        )
        resp.raise_for_status()
        generated = resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return JsonResponse({'error': f'Błąd OpenAI: {str(e)}'}, status=500)

    # Dodaj odpowiedź AI do historii
    messages.append({'role': 'assistant', 'content': generated})

    return JsonResponse({
        'ok': True,
        'generated': generated,
        'messages': messages,
        'char_count': len(generated),
    })


@login_required
def content_list_all(request):
    """Globalna lista wszystkich postów content."""
    from django.core.paginator import Paginator

    posts = (
        ContentPost.objects
        .select_related('lead', 'lead__city')
        .prefetch_related('versions')
        .filter(lead__status='client')
        .order_by('-updated_at')
    )

    # Filtr po kanale
    channel_filter = request.GET.get('channel', '')
    if channel_filter:
        posts = posts.filter(channel=channel_filter)

    # Filtr po statusach (wielokrotny)
    status_filters = request.GET.getlist('status')
    # Domyślnie wszystkie statusy poza 'published'
    default_statuses = [v for v, _ in ContentPost.STATUS_CHOICES if v != ContentPost.STATUS_PUBLISHED]
    if not status_filters and 'status' not in request.GET:
        status_filters = default_statuses
    if status_filters:
        posts = posts.filter(status__in=status_filters)

    # Dołącz aktualną wersję
    for post in posts:
        post.current_ver = post.versions.filter(is_current=True).first()

    paginator = Paginator(posts, 25)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'leads/content/list_all.html', {
        'page': page,
        'total_count': paginator.count,
        'channel_choices': ContentPost.CHANNEL_CHOICES,
        'status_choices': ContentPost.STATUS_CHOICES,
        'channel_filter': channel_filter,
        'status_filters': status_filters,
    })


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

    from ..models import BrandProfile
    try:
        brand = lead.brand_profile
    except BrandProfile.DoesNotExist:
        brand = None

    idea_categories = PostIdeaCategory.objects.prefetch_related('ideas').all()

    return render(request, 'leads/content/form.html', {
        'lead': lead,
        'post': None,
        'version': None,
        'status_choices': ContentPost.STATUS_CHOICES,
        'channel_choices': ContentPost.CHANNEL_CHOICES,
        'type_choices': ContentPost.TYPE_CHOICES,
        'brand': brand,
        'idea_categories': idea_categories,
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
                notes='',
                is_current=True,
                created_by=request.user,
            )
            post.status = ContentPost.STATUS_REVIEW
            post.save(update_fields=['updated_at', 'status'])

        elif action == 'delete':
            post.delete()
            return redirect('leads:content_index', lead_pk=lead.pk)

        return redirect('leads:content_detail', lead_pk=lead.pk, post_pk=post.pk)

    from ..models import BrandProfile
    try:
        brand = lead.brand_profile
    except BrandProfile.DoesNotExist:
        brand = None

    idea_categories = PostIdeaCategory.objects.prefetch_related('ideas').all()

    # Dane wszystkich wersji do modalu podglądu
    import json as _json
    versions_data = [
        {
            'pk': v.pk,
            'version_number': v.version_number,
            'is_current': v.is_current,
            'title': v.title,
            'body': v.body,
            'drive_url': v.drive_url,
            'drive_preview_url': v.drive_preview_url or '',
            'cta_text': v.cta_text,
            'cta_url': v.cta_url,
            'notes': v.notes,
            'created_at': v.created_at.strftime('%d.%m.%Y %H:%M'),
            'created_by': v.created_by.get_full_name() or v.created_by.username if v.created_by else '',
        }
        for v in history
    ]

    return render(request, 'leads/content/detail.html', {
        'lead': lead,
        'post': post,
        'current': current,
        'history': history,
        'status_choices': ContentPost.STATUS_CHOICES,
        'brand': brand,
        'idea_categories': idea_categories,
        'versions_json': _json.dumps(versions_data, ensure_ascii=False),
    })
