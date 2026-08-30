import random

from django.shortcuts import render

from apps.content.models import Content
from apps.subscriptions.models import Subscription
from apps.users.models import User
from apps.content.queries import visible_content_filter


def home(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    is_search = bool(query or category_slug)

    if is_search:
        content_items, discover_creators = _search(query, category_slug)
    else:
        content_items, discover_creators = _random_feed()

    _annotate_lock_state(request, content_items)

    context = {
        'content_items': content_items,
        'discover_creators': discover_creators,
        'is_search': is_search,
        'search_query': query,
        'search_category': category_slug,
    }
    return render(request, 'core/home.html', context)


def _random_feed():
    content_pool = list(
        Content.objects
        .filter(is_published=True)
        .select_related(
            'creator', 'creator__creator_profile', 'creator__creator_profile__category',
            'minimum_tier',
        )
        .order_by('-created_at')[:100]
    )
    random.shuffle(content_pool)
    content_items = content_pool[:20]

    discover_creators = (
        User.objects
        .filter(is_creator=True)
        .select_related('creator_profile', 'creator_profile__category')
        .order_by('?')[:6]
    )
    return content_items, discover_creators


def _search(query, category_slug):
    creators_qs = (
        User.objects
        .filter(is_creator=True)
        .select_related('creator_profile', 'creator_profile__category')
    )
    if query:
        creators_qs = creators_qs.filter(display_name__icontains=query)
    if category_slug:
        creators_qs = creators_qs.filter(creator_profile__category__slug=category_slug)

    discover_creators = list(creators_qs[:12])

    content_items = list(
        Content.objects
        .filter(is_published=True, creator__in=creators_qs)
        .select_related(
            'creator', 'creator__creator_profile', 'creator__creator_profile__category',
            'minimum_tier',
        )
        .order_by('-created_at')[:30]
    )
    return content_items, discover_creators


def _annotate_lock_state(request, content_items):
    subscriber_levels = {}
    if request.user.is_authenticated:
        subscriber_levels = dict(
            Subscription.objects
            .filter(subscriber=request.user, status=Subscription.Status.ACTIVE)
            .values_list('creator_id', 'tier__level')
        )

    for item in content_items:
        if item.creator_id == request.user.id:
            item.is_locked = False
        elif item.minimum_tier_id is None:
            item.is_locked = False
        else:
            my_level = subscriber_levels.get(item.creator_id)
            item.is_locked = my_level is None or my_level < item.minimum_tier.level