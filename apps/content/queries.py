from django.db.models import Q
from django.utils import timezone


def visible_content_filter(prefix=''):
    """
    A piece of content is visible to the public only if it's marked
    published AND either has no schedule (published immediately) or its
    scheduled time has already passed. Centralized here so the feed, the
    search, and profile pages can't drift out of sync on this rule.
    """
    return Q(**{f'{prefix}is_published': True}) & (
        Q(**{f'{prefix}published_at__isnull': True})
        | Q(**{f'{prefix}published_at__lte': timezone.now()})
    )
