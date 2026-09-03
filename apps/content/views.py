from django.contrib import messages
from django.db.models import Count, Exists, OuterRef, Subquery, Value
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from apps.users.decorators import creator_required

from .forms import ContentForm, CollectionForm
from .models import Comment, Content, ContentHistory, ContentLike, Collection, SavedItem
from .access import annotate_lock_state
from .queries import social_queryset, visible_content_filter


def public_collection_detail(request, pk):
    """Show a creator's public collection and its currently visible items."""
    collection_qs = Collection.objects.select_related(
        'creator',
        'creator__creator_profile',
        'creator__creator_profile__category',
        'minimum_tier',
    )
    if request.user.is_authenticated:
        collection_qs = collection_qs.annotate(
            user_has_saved=Exists(
                SavedItem.objects.filter(collection_id=OuterRef('pk'), user=request.user)
            )
        )
    collection = get_object_or_404(collection_qs, pk=pk)

    content_items = list(
        social_queryset(request, collection.items.filter(visible_content_filter())
        .select_related(
            'creator',
            'creator__creator_profile',
            'creator__creator_profile__category',
            'minimum_tier',
        )
        .order_by('order', '-created_at'))
    )
    annotate_lock_state(request, content_items)

    return render(
        request,
        'content/collection_detail.html',
        {
            'collection': collection,
            'content_items': content_items,
        },
    )


def public_content_detail(request, pk):
    """Render one public content item in a distraction-free player view."""
    item = get_object_or_404(
        social_queryset(
            request,
            Content.objects.filter(visible_content_filter()).select_related(
                'creator',
                'creator__creator_profile',
                'creator__creator_profile__category',
                'minimum_tier',
                'collection',
            ),
        ),
        pk=pk,
    )
    annotate_lock_state(request, [item])

    resume_position = 0
    if request.user.is_authenticated and not item.is_locked:
        history, _ = ContentHistory.objects.get_or_create(
            user=request.user,
            content=item,
        )
        resume_position = history.progress_seconds if not history.completed else 0

    return render(
        request,
        'content/content_detail.html',
        {
            'item': item,
            'resume_position': resume_position,
        },
    )


@login_required
@require_POST
def update_content_history(request, pk):
    """Persist video playback progress without affecting the public player."""
    content = get_object_or_404(
        Content.objects.filter(visible_content_filter()).select_related('minimum_tier'),
        pk=pk,
    )
    annotate_lock_state(request, [content])
    if content.is_locked:
        return JsonResponse({'error': 'Subscribe to this creator to watch this content.'}, status=403)

    try:
        position = max(0.0, float(request.POST.get('position', 0)))
    except (TypeError, ValueError):
        position = 0.0

    try:
        duration_raw = request.POST.get('duration', '')
        duration = max(0.0, float(duration_raw)) if duration_raw else None
    except (TypeError, ValueError):
        duration = None

    completed = request.POST.get('completed') == 'true'
    if duration and position >= max(duration - 2, 0):
        completed = True

    history, _ = ContentHistory.objects.get_or_create(
        user=request.user,
        content=content,
    )
    history.progress_seconds = position
    history.duration_seconds = duration
    history.completed = completed
    history.save(update_fields=['last_viewed_at', 'progress_seconds', 'duration_seconds', 'completed'])

    return JsonResponse({'saved': True, 'completed': completed})


@login_required
@require_POST
def toggle_content_save(request, pk):
    content = get_object_or_404(
        Content.objects.filter(visible_content_filter()),
        pk=pk,
    )
    saved, created = SavedItem.objects.get_or_create(
        user=request.user,
        content=content,
    )
    if not created:
        saved.delete()
    return JsonResponse({'saved': created})


@login_required
@require_POST
def toggle_collection_save(request, pk):
    collection = get_object_or_404(Collection, pk=pk)
    saved, created = SavedItem.objects.get_or_create(
        user=request.user,
        collection=collection,
    )
    if not created:
        saved.delete()
    return JsonResponse({'saved': created})


@login_required
def history(request):
    entries = (
        ContentHistory.objects
        .filter(user=request.user, content__isnull=False)
        .select_related(
            'content',
            'content__creator',
            'content__creator__creator_profile',
            'content__creator__creator_profile__category',
            'content__minimum_tier',
            'content__collection',
        )
        .filter(content__in=Content.objects.filter(visible_content_filter()))
        .order_by('-last_viewed_at')
    )

    history_items = []
    for entry in entries:
        item = entry.content
        item.history_viewed_at = entry.last_viewed_at
        item.history_progress_seconds = entry.progress_seconds
        item.history_duration_seconds = entry.duration_seconds
        item.history_completed = entry.completed
        if entry.duration_seconds and entry.duration_seconds > 0:
            item.history_progress_percent = min(100, round((entry.progress_seconds / entry.duration_seconds) * 100))
        else:
            item.history_progress_percent = 0
        history_items.append(item)

    annotate_lock_state(request, history_items)
    return render(request, 'content/history.html', {'history_items': history_items})


@login_required
def saved_for_later(request):
    saved_content = SavedItem.objects.filter(
        user=request.user, content__isnull=False
    )
    saved_collections = SavedItem.objects.filter(
        user=request.user, collection__isnull=False
    )

    content_items = list(
        social_queryset(
            request,
            Content.objects.filter(
                visible_content_filter(),
                id__in=saved_content.values('content_id'),
            ).select_related(
                'creator',
                'creator__creator_profile',
                'creator__creator_profile__category',
                'minimum_tier',
                'collection',
            ).annotate(
                saved_at=Subquery(
                    saved_content.filter(content_id=OuterRef('pk')).values('created_at')[:1]
                )
            ).order_by('-saved_at'),
        )
    )
    annotate_lock_state(request, content_items)

    collections = list(
        Collection.objects.filter(
            id__in=saved_collections.values('collection_id')
        ).select_related(
            'creator',
            'creator__creator_profile',
            'creator__creator_profile__category',
            'minimum_tier',
        ).annotate(
            user_has_saved=Value(True),
            saved_at=Subquery(
                saved_collections.filter(collection_id=OuterRef('pk')).values('created_at')[:1]
            ),
            visible_item_count=Count(
                'items',
                filter=visible_content_filter(prefix='items__'),
            ),
        ).order_by('-saved_at')
    )

    return render(
        request,
        'content/saved_for_later.html',
        {
            'saved_content': content_items,
            'saved_collections': collections,
        },
    )


@login_required
@require_POST
def toggle_like(request, pk):
    content = get_object_or_404(
        Content.objects.filter(visible_content_filter()).select_related('minimum_tier'),
        pk=pk,
    )
    annotate_lock_state(request, [content])
    if content.is_locked:
        return JsonResponse({'error': 'Subscribe to this creator to interact with this content.'}, status=403)

    like, created = ContentLike.objects.get_or_create(content=content, user=request.user)
    if not created:
        like.delete()
    return JsonResponse({
        'liked': created,
        'count': ContentLike.objects.filter(content=content).count(),
    })


@login_required
@require_POST
def create_comment(request, pk):
    content = get_object_or_404(
        Content.objects.filter(visible_content_filter()).select_related('minimum_tier'),
        pk=pk,
    )
    annotate_lock_state(request, [content])
    if content.is_locked:
        return JsonResponse({'error': 'Subscribe to this creator to comment on this content.'}, status=403)

    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'error': 'Comment cannot be empty.'}, status=400)
    comment = Comment.objects.create(content=content, author=request.user, body=body)
    return JsonResponse({
        'id': comment.id,
        'body': comment.body,
        'author_name': comment.author.display_name,
        'author_initial': comment.author.display_name[:1].upper(),
        'author_avatar_url': comment.author.avatar.url if comment.author.avatar else '',
        'author_avatar_position_x': comment.author.avatar_position_x,
        'author_avatar_position_y': comment.author.avatar_position_y,
        'created_at': comment.created_at.isoformat(),
        'time_ago': 'just now',
        'count': Comment.objects.filter(content=content).count(),
    })


@creator_required
def creator_content_new(request):
    if request.method == 'POST':
        form = ContentForm(
            request.POST,
            request.FILES,
            creator=request.user,
        )

        if form.is_valid():
            content = form.save()

            if content.published_at > timezone.now():
                messages.success(
                    request,
                    f'Scheduled for {content.published_at:%B %d, %Y %H:%M}.'
                )
            else:
                messages.success(
                    request,
                    'Content published.'
                )

            return redirect('creator_content:new')

    else:
        form = ContentForm(
            creator=request.user
        )

    return render(
        request,
        'creator_dashboard/content_new.html',
        {
            'form': form,
            'active_tab': 'new_content',
        },
    )


@creator_required
def creator_content_list(request):
    content_items = (
        request.user.content_items
        .select_related('minimum_tier', 'collection')
        .order_by('-created_at')
    )

    return render(
        request,
        'creator_dashboard/content_list.html',
        {
            'content_items': content_items,
            'now': timezone.now(),
            'active_tab': 'content',
        },
    )


@creator_required
def creator_content_edit(request, pk):
    content = get_object_or_404(
        Content,
        pk=pk,
        creator=request.user,
    )

    if request.method == 'POST':
        form = ContentForm(
            request.POST,
            request.FILES,
            instance=content,
            creator=request.user,
            include_publish_fields=False,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Content updated.'
            )

            return redirect('creator_content:list')

    else:
        form = ContentForm(
            instance=content,
            creator=request.user,
            include_publish_fields=False,
        )

    return render(
        request,
        'creator_dashboard/content_edit.html',
        {
            'form': form,
            'content': content,
            'active_tab': 'content',
        },
    )


@creator_required
@require_POST
def creator_content_delete(request, pk):
    content = get_object_or_404(
        Content,
        pk=pk,
        creator=request.user,
    )

    content.delete()

    messages.success(
        request,
        'Content deleted.'
    )

    return redirect('creator_content:list')


@creator_required
def creator_collection_list(request):
    collections = (
        request.user.collections
        .annotate(item_count=Count('items'))
        .order_by('-created_at')
    )

    if request.method == 'POST':
        form = CollectionForm(
            request.POST,
            request.FILES,
            creator=request.user,
        )

        if form.is_valid():
            collection = form.save(commit=False)
            collection.creator = request.user
            collection.save()

            messages.success(
                request,
                'Collection created.'
            )

            return redirect(
                'creator_content:collection_list'
            )

    else:
        form = CollectionForm(
            creator=request.user
        )

    return render(
        request,
        'creator_dashboard/collection_list.html',
        {
            'form': form,
            'collections': collections,
            'active_tab': 'collections',
        },
    )


@creator_required
def creator_collection_edit(request, pk):
    collection = get_object_or_404(
        Collection,
        pk=pk,
        creator=request.user,
    )

    all_content = (
        request.user.content_items
        .order_by('-created_at')
    )

    current_ids = set(
        collection.items.values_list(
            'id',
            flat=True,
        )
    )

    if request.method == 'POST':
        form = CollectionForm(
            request.POST,
            request.FILES,
            instance=collection,
            creator=request.user,
        )

        if form.is_valid():
            collection = form.save()

            selected_ids = {
                int(i)
                for i in request.POST.getlist('content_items')
            }

            # Items removed from the Collection are detached,
            # but keep their current minimum_tier.
            removed_ids = current_ids - selected_ids

            Content.objects.filter(
                id__in=removed_ids,
                creator=request.user,
            ).update(
                collection=None
            )

            # Items inside the Collection always inherit
            # the Collection's minimum_tier.
            Content.objects.filter(
                id__in=selected_ids,
                creator=request.user,
            ).update(
                collection=collection,
                minimum_tier=collection.minimum_tier,
            )

            messages.success(
                request,
                'Collection updated.'
            )

            return redirect(
                'creator_content:collection_list'
            )

    else:
        form = CollectionForm(
            instance=collection,
            creator=request.user,
        )

    return render(
        request,
        'creator_dashboard/collection_edit.html',
        {
            'form': form,
            'collection': collection,
            'all_content': all_content,
            'current_ids': current_ids,
            'active_tab': 'collections',
        },
    )
