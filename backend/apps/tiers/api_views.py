from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import ValidationError

from .models import Tier
from .services import sync_tier_to_stripe


class IsCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_creator)


class TierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tier
        fields = ['id', 'name', 'description', 'price', 'level', 'is_active', 'created_at']
        read_only_fields = ['id', 'is_active', 'created_at']

    def validate_level(self, level):
        user = self.context['request'].user
        conflict = Tier.objects.filter(creator=user, level=level, is_active=True)
        if self.instance:
            conflict = conflict.exclude(pk=self.instance.pk)
        if conflict.exists():
            raise ValidationError('An active tier already uses this level.')
        return level


class TierListView(generics.ListCreateAPIView):
    permission_classes = [IsCreator]
    serializer_class = TierSerializer
    pagination_class = None

    def get_queryset(self):
        return Tier.objects.filter(creator=self.request.user, is_active=True).order_by('level')

    def perform_create(self, serializer):
        if self.get_queryset().count() >= 3:
            raise ValidationError('A creator can have at most three active tiers.')
        tier = serializer.save(creator=self.request.user)
        sync_tier_to_stripe(tier)


class TierDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsCreator]
    serializer_class = TierSerializer

    def get_queryset(self):
        return Tier.objects.filter(creator=self.request.user, is_active=True)

    def perform_update(self, serializer):
        tier = serializer.save()
        sync_tier_to_stripe(tier)

    def perform_destroy(self, instance):
        # Keep subscription history intact; removal means deactivation.
        instance.is_active = False
        instance.save(update_fields=['is_active'])
