from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ..models import LeadTask, TaskComment
import json


@login_required
def task_comments(request, task_pk):
    """Pobiera komentarze do zadania (GET) lub dodaje nowy (POST)."""
    task = get_object_or_404(LeadTask, pk=task_pk)

    if request.method == 'GET':
        comments = task.comments.filter(parent__isnull=True).prefetch_related(
            'replies__author', 'author'
        )
        return JsonResponse({
            'ok': True,
            'task_title': task.title,
            'task_lead': task.lead.name,
            'comments': [_serialize_comment(c, include_replies=True) for c in comments],
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'B\u0142\u0105d danych'}, status=400)

        body = data.get('body', '').strip()
        parent_pk = data.get('parent_pk')

        if not body:
            return JsonResponse({'error': 'Tre\u015b\u0107 komentarza nie mo\u017ce by\u0107 pusta'}, status=400)

        parent = None
        if parent_pk:
            parent = get_object_or_404(TaskComment, pk=parent_pk, task=task, parent__isnull=True)

        comment = TaskComment.objects.create(
            task=task,
            parent=parent,
            author=request.user,
            body=body,
        )
        return JsonResponse({'ok': True, 'comment': _serialize_comment(comment)})

    return JsonResponse({'error': 'method not allowed'}, status=405)


@login_required
def task_comment_delete(request, task_pk, comment_pk):
    """Usuwa komentarz (tylko autor lub superuser)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    comment = get_object_or_404(TaskComment, pk=comment_pk, task_id=task_pk)
    if comment.author != request.user and not request.user.is_superuser:
        return JsonResponse({'error': 'Brak uprawnie\u0144'}, status=403)

    comment.delete()
    return JsonResponse({'ok': True})


def _serialize_comment(comment, include_replies=False):
    data = {
        'pk': comment.pk,
        'body': comment.body,
        'author': comment.author.get_full_name() or comment.author.username if comment.author else 'Usuni\u0119ty',
        'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M'),
        'is_reply': comment.parent_id is not None,
        'replies': [],
    }
    if include_replies:
        data['replies'] = [_serialize_comment(r) for r in comment.replies.all()]
    return data
