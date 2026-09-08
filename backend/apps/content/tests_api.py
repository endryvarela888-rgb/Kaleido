from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content.models import Category, Comment, Content, ContentLike
from apps.tiers.models import Tier
from apps.users.models import CreatorProfile, User


class ContentApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.creator = User.objects.create_user(email='creator@example.com', password='password123', display_name='Creator', is_creator=True)
        CreatorProfile.objects.create(user=self.creator, category=Category.objects.create(name='Music'))
        self.viewer = User.objects.create_user(email='viewer@example.com', password='password123', display_name='Viewer')
        self.content = Content.objects.create(
            creator=self.creator, content_type=Content.ContentType.TEXT, title='Public post',
            is_published=True, published_at=timezone.now(),
        )

    def test_feed_returns_persisted_engagement_counts(self):
        ContentLike.objects.create(content=self.content, user=self.viewer)
        Comment.objects.create(content=self.content, author=self.viewer, body='Great work')
        response = self.client.get('/api/content/feed/')
        self.assertEqual(response.status_code, 200)
        item = response.data['results'][0]
        self.assertEqual(item['like_count'], 1)
        self.assertEqual(item['comment_count'], 1)

    def test_only_creator_can_use_creator_content_api(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post('/api/content/creator/content/', {'title': 'Nope'})
        self.assertEqual(response.status_code, 403)

    def test_locked_content_rejects_interaction(self):
        tier = Tier.objects.create(creator=self.creator, name='Gold', price=10, level=1)
        self.content.minimum_tier = tier
        self.content.save(update_fields=['minimum_tier'])
        self.client.force_authenticate(self.viewer)
        response = self.client.post(f'/api/content/{self.content.id}/like/')
        self.assertEqual(response.status_code, 403)
