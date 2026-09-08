from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Top-level classification for creators/content (e.g. Music, Gaming,
    Writing). Kept as its own model — not a hardcoded choices list — so
    admins can add new categories without touching code.
    """

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Collection(models.Model):
    """
    A folder/playlist grouping related Content together (e.g. a multi-part
    video series). A piece of Content belongs to at most one Collection.

    Every Content inside a Collection inherits this Collection's
    minimum_tier.
    """

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='collections',
        limit_choices_to={'is_creator': True},
    )
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to='collections/covers/',
        blank=True,
        null=True,
    )

    minimum_tier = models.ForeignKey(
        'tiers.Tier',
        on_delete=models.SET_NULL,
        related_name='collections_with_tier',
        null=True,
        blank=True,
        help_text='Minimum subscription tier required to access this collection.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Content(models.Model):
    """
    A single piece of content published by a creator: a video, an image,
    an audio file, or a text post.

    Content can optionally belong to a Collection. If it belongs to a
    Collection, its minimum_tier is always inherited from that Collection.
    """

    class ContentType(models.TextChoices):
        VIDEO = 'video', 'Video'
        IMAGE = 'image', 'Image'
        AUDIO = 'audio', 'Audio'
        TEXT = 'text', 'Text'

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='content_items',
        limit_choices_to={'is_creator': True},
    )

    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        related_name='items',
        null=True,
        blank=True,
    )

    minimum_tier = models.ForeignKey(
        'tiers.Tier',
        on_delete=models.SET_NULL,
        related_name='gated_content',
        null=True,
        blank=True,
        help_text='Minimum subscription tier required to access this content.',
    )

    content_type = models.CharField(
        max_length=10,
        choices=ContentType.choices,
    )

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    media_file = models.FileField(
        upload_to='content/media/',
        blank=True,
        null=True,
    )

    thumbnail = models.ImageField(
        upload_to='content/thumbnails/',
        blank=True,
        null=True,
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text='Position within its Collection, if any.',
    )

    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['collection', 'order', '-created_at']

    def __str__(self):
        return self.title

class ContentLike(models.Model):
    """A persistent like from one user on one piece of content."""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='content_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content', 'user'],
                name='unique_content_like_per_user',
            ),
        ]
        ordering = ['-created_at']


class Comment(models.Model):
    """A user comment attached to a piece of content."""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='content_comments')
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} on {self.content}'


class SavedItem(models.Model):
    """A user's saved-for-later bookmark for either Content or Collection."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_items',
    )
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='saved_by',
        null=True,
        blank=True,
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name='saved_by',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'content'],
                condition=models.Q(content__isnull=False),
                name='unique_saved_content_per_user',
            ),
            models.UniqueConstraint(
                fields=['user', 'collection'],
                condition=models.Q(collection__isnull=False),
                name='unique_saved_collection_per_user',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(content__isnull=False, collection__isnull=True)
                    | models.Q(content__isnull=True, collection__isnull=False)
                ),
                name='saved_item_exactly_one_target',
            ),
        ]

    def __str__(self):
        target = self.content or self.collection
        return f'{self.user} saved {target}'

class ContentHistory(models.Model):
    """The last time a user viewed a piece of content and its media progress."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='content_history',
    )
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='history_entries',
    )
    last_viewed_at = models.DateTimeField(auto_now=True)
    progress_seconds = models.FloatField(default=0)
    duration_seconds = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_viewed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'content'],
                name='unique_content_history_per_user',
            ),
        ]

    def __str__(self):
        return f'{self.user} viewed {self.content}'

