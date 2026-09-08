from rest_framework import serializers
from django.utils import timezone

from apps.tiers.models import Tier
from apps.users.serializers import UserSerializer

from .models import Category, Collection, Comment, Content
from .utils import guess_content_type


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class TierMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tier
        fields = ['id', 'name', 'price', 'level']


class ContentSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    minimum_tier = TierMinimalSerializer(read_only=True)
    media_file = serializers.FileField(read_only=True)
    thumbnail = serializers.ImageField(read_only=True)

    is_locked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    collection_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Content
        fields = [
            'id', 'creator', 'content_type', 'title', 'description',
            'media_file', 'thumbnail', 'minimum_tier', 'collection_id', 'is_locked',
            'like_count', 'user_has_liked', 'comment_count', 'created_at',
        ]

    def get_is_locked(self, obj):
        return getattr(obj, 'is_locked', False)

    def get_like_count(self, obj):
        return getattr(obj, 'likes_count', 0)

    def get_user_has_liked(self, obj):
        return getattr(obj, 'user_has_liked', False)

    def get_comment_count(self, obj):
        return getattr(obj, 'comments_count', 0)


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'body', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class CollectionSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    minimum_tier = TierMinimalSerializer(read_only=True)
    item_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Collection
        fields = ['id', 'creator', 'title', 'description', 'cover_image', 'minimum_tier', 'item_count', 'created_at', 'updated_at']


class CreatorContentSerializer(serializers.ModelSerializer):
    """Write serializer that never accepts a creator id from the client."""
    publish_at = serializers.DateTimeField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Content
        fields = ['id', 'title', 'description', 'media_file', 'thumbnail', 'collection', 'minimum_tier', 'publish_at', 'is_published', 'published_at']
        read_only_fields = ['id', 'is_published', 'published_at']

    def validate(self, attrs):
        user = self.context['request'].user
        collection = attrs.get('collection', getattr(self.instance, 'collection', None))
        tier = attrs.get('minimum_tier', getattr(self.instance, 'minimum_tier', None))
        if collection and collection.creator_id != user.id:
            raise serializers.ValidationError({'collection': 'Choose one of your own collections.'})
        if tier and tier.creator_id != user.id:
            raise serializers.ValidationError({'minimum_tier': 'Choose one of your own tiers.'})
        publish_at = attrs.get('publish_at')
        if publish_at and publish_at <= timezone.now():
            raise serializers.ValidationError({'publish_at': 'The scheduled time must be in the future.'})
        return attrs

    def _apply_access_and_type(self, instance, validated_data):
        validated_data.pop('publish_at', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if instance.collection_id:
            instance.minimum_tier = instance.collection.minimum_tier
        source_name = instance.media_file.name if instance.media_file else None
        instance.content_type = guess_content_type(source_name)
        return instance

    def create(self, validated_data):
        publish_at = validated_data.pop('publish_at', None)
        instance = Content(creator=self.context['request'].user, is_published=True, published_at=publish_at or timezone.now())
        instance = self._apply_access_and_type(instance, validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        instance = self._apply_access_and_type(instance, validated_data)
        instance.save()
        return instance


class CreatorCollectionSerializer(serializers.ModelSerializer):
    content_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Content.objects.all(), write_only=True, required=False,
    )

    class Meta:
        model = Collection
        fields = ['id', 'title', 'description', 'cover_image', 'minimum_tier', 'content_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_minimum_tier(self, tier):
        if tier and tier.creator_id != self.context['request'].user.id:
            raise serializers.ValidationError('Choose one of your own tiers.')
        return tier

    def validate_content_ids(self, content_items):
        user = self.context['request'].user
        if any(item.creator_id != user.id for item in content_items):
            raise serializers.ValidationError('Only your content can be added to a collection.')
        return content_items

    def create(self, validated_data):
        content_items = validated_data.pop('content_ids', [])
        collection = Collection.objects.create(creator=self.context['request'].user, **validated_data)
        Content.objects.filter(pk__in=[item.pk for item in content_items]).update(collection=collection, minimum_tier=collection.minimum_tier)
        return collection

    def update(self, instance, validated_data):
        content_items = validated_data.pop('content_ids', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if content_items is not None:
            selected_ids = [item.pk for item in content_items]
            instance.items.exclude(pk__in=selected_ids).update(collection=None)
            Content.objects.filter(pk__in=selected_ids).update(collection=instance, minimum_tier=instance.minimum_tier)
        else:
            instance.items.update(minimum_tier=instance.minimum_tier)
        return instance
