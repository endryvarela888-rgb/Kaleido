from django.db.models import BooleanField, Count, Exists, OuterRef, Prefetch, Q, Value
from django.utils import timezone

from .models import Comment, ContentLike, SavedItem


def social_queryset(request, queryset):
    """Annotate content with persistent like state/count and recent comments."""
    queryset = queryset.annotate(likes_count=Count('likes', distinct=True), comments_count=Count('comments', distinct=True))
    if request.user.is_authenticated:
        queryset = queryset.annotate(
            user_has_liked=Exists(
                ContentLike.objects.filter(content_id=OuterRef('pk'), user=request.user)
            )
        )
    else:
        queryset = queryset.annotate(user_has_liked=Value(False, output_field=BooleanField()))

    recent_comments = Comment.objects.select_related('author').order_by('-created_at')[:5]
    if request.user.is_authenticated:
        queryset = queryset.annotate(
            user_has_saved=Exists(
                SavedItem.objects.filter(content_id=OuterRef('pk'), user=request.user)
            )
        )
    else:
        queryset = queryset.annotate(user_has_saved=Value(False, output_field=BooleanField()))
    return queryset.prefetch_related(
        Prefetch('comments', queryset=recent_comments, to_attr='recent_comments')
    )


def visible_content_filter(prefix=''):
    """
    A piece of Content is visible only if it is published and its scheduled
    publication time has arrived (or is not set).
    """
    return Q(**{f'{prefix}is_published': True}) & (
        Q(**{f'{prefix}published_at__isnull': True})
        | Q(**{f'{prefix}published_at__lte': timezone.now()})
    )
