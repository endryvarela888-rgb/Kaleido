from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.users.decorators import creator_required

from .forms import ContentForm, CollectionForm
from .models import Content, Collection
from .access import annotate_lock_state
from .queries import visible_content_filter


def public_collection_detail(request, pk):
    """Show a creator's public collection and its currently visible items."""
    collection = get_object_or_404(
        Collection.objects.select_related(
            'creator',
            'creator__creator_profile',
            'creator__creator_profile__category',
            'minimum_tier',
        ),
        pk=pk,
    )

    content_items = list(
        collection.items.filter(visible_content_filter())
        .select_related(
            'creator',
            'creator__creator_profile',
            'creator__creator_profile__category',
            'minimum_tier',
        )
        .order_by('order', '-created_at')
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
        Content.objects.filter(visible_content_filter()).select_related(
            'creator',
            'creator__creator_profile',
            'creator__creator_profile__category',
            'minimum_tier',
            'collection',
        ),
        pk=pk,
    )
    annotate_lock_state(request, [item])

    return render(request, 'content/content_detail.html', {'item': item})


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
