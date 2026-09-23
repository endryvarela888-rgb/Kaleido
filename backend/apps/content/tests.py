from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import pytest


from .models import Collection, SavedItem, Content, ContentLike, Comment

User = get_user_model()

class SocialContentTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(email='creator@example.com', password='testpass123', is_creator=True, display_name='Creator')
        self.user = User.objects.create_user(email='user@example.com', password='testpass123', display_name='User')
        self.content = Content.objects.create(
            creator=self.creator,
            content_type=Content.ContentType.TEXT,
            title='Test content',
            description='A test post',
            is_published=True,
        )

    def test_like_persists_and_toggles(self):
        self.client.force_login(self.user)
        url = reverse('content:content_like', args=[self.content.pk])

        response = self.client.post(url)
        self.assertJSONEqual(response.content, {'liked': True, 'count': 1})
        self.assertTrue(ContentLike.objects.filter(content=self.content, user=self.user).exists())

        response = self.client.post(url)
        self.assertJSONEqual(response.content, {'liked': False, 'count': 0})
        self.assertFalse(ContentLike.objects.filter(content=self.content, user=self.user).exists())

    def test_comment_can_be_created(self):
        self.client.force_login(self.user)
        url = reverse('content:content_comment', args=[self.content.pk])

        response = self.client.post(url, {'body': 'Hello from a test comment'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().body, 'Hello from a test comment')

    def test_comment_requires_authentication(self):
        url = reverse('content:content_comment', args=[self.content.pk])
        response = self.client.post(url, {'body': 'Should not be posted'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)


class SavedForLaterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='saved@example.com',
            password='StrongPass123!',
            display_name='Saved User',
        )
        self.creator = User.objects.create_user(
            email='creator@example.com',
            password='StrongPass123!',
            display_name='Creator',
            is_creator=True,
        )
        self.content = Content.objects.create(
            creator=self.creator,
            content_type=Content.ContentType.TEXT,
            title='Saved post',
            description='A post to save.',
            is_published=True,
        )
        self.collection = Collection.objects.create(
            creator=self.creator,
            title='Saved collection',
            description='A collection to save.',
        )

    def test_content_can_be_saved_and_unsaved(self):
        self.client.force_login(self.user)
        url = reverse('content:content_save', kwargs={'pk': self.content.pk})
        response = self.client.post(url)
        self.assertJSONEqual(response.content, {'saved': True})
        self.assertTrue(SavedItem.objects.filter(user=self.user, content=self.content).exists())

        response = self.client.post(url)
        self.assertJSONEqual(response.content, {'saved': False})
        self.assertFalse(SavedItem.objects.filter(user=self.user, content=self.content).exists())

    @pytest.mark.skip(reason="Vista legacy de Django templates, reemplazada por el frontend de React")
    def test_collection_can_be_saved_and_saved_page_separates_sections(self):
        self.client.force_login(self.user)
        self.client.post(reverse('content:content_save', kwargs={'pk': self.content.pk}))
        self.client.post(reverse('content:collection_save', kwargs={'pk': self.collection.pk}))

        response = self.client.get(reverse('content:saved'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['saved_content']), [self.content])
        self.assertEqual(list(response.context['saved_collections']), [self.collection])

    def test_anonymous_save_redirects_to_login(self):
        response = self.client.post(reverse('content:content_save', kwargs={'pk': self.content.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/users/login/', response['Location'])
