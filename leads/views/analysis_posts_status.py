from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from leads.models import Lead, GoogleBusinessAnalysis


@login_required
def analysis_posts_status(request, pk, analysis_pk):
    get_object_or_404(Lead, pk=pk)
    analysis = get_object_or_404(GoogleBusinessAnalysis, pk=analysis_pk, lead_id=pk)

    last_post = analysis.last_post_date.isoformat() if analysis.last_post_date else None
    posts_label = None
    if analysis.posts_status == 'fetched':
        if analysis.has_posts:
            count = f"{analysis.posts_count}+" if analysis.posts_count_plus else str(analysis.posts_count)
            posts_label = f"{count} postów, ostatni: {last_post}" if last_post else f"{count} postów"
        else:
            posts_label = "Brak postów"

    return JsonResponse({
        'posts_status': analysis.posts_status,
        'has_posts': analysis.has_posts,
        'posts_count': analysis.posts_count,
        'posts_count_plus': analysis.posts_count_plus,
        'last_post_date': last_post,
        'posts_label': posts_label,
    })
