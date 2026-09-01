from apps.subscriptions.models import Subscription


def annotate_lock_state(request, content_items):
    """Attach the presentation-only ``is_locked`` flag to public content."""
    subscriber_levels = {}

    if request.user.is_authenticated:
        subscriber_levels = dict(
            Subscription.objects.filter(
                subscriber=request.user,
                status=Subscription.Status.ACTIVE,
            ).values_list('creator_id', 'tier__level')
        )

    for item in content_items:
        if item.creator_id == request.user.id or item.minimum_tier_id is None:
            item.is_locked = False
            continue

        subscriber_level = subscriber_levels.get(item.creator_id)
        item.is_locked = (
            subscriber_level is None
            or subscriber_level < item.minimum_tier.level
        )
