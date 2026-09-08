from rest_framework import permissions
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.users.serializers import UserSerializer
from apps.content.serializers import TierMinimalSerializer
from . import services
from .models import Subscription


def subscription_data(subscription, request):
    return {
        'id': subscription.id,
        'creator': UserSerializer(subscription.creator, context={'request': request}).data,
        'tier': TierMinimalSerializer(subscription.tier).data,
        'pending_tier': TierMinimalSerializer(subscription.pending_tier).data if subscription.pending_tier else None,
        'current_period_end': subscription.current_period_end,
        'cancel_at_period_end': subscription.cancel_at_period_end,
    }


class MySubscriptionsView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def list(self, request, *args, **kwargs):
        subscriptions = Subscription.objects.filter(
            subscriber=request.user, status=Subscription.Status.ACTIVE,
        ).select_related('creator', 'creator__creator_profile', 'creator__creator_profile__category', 'tier', 'pending_tier').order_by('current_period_end')
        return Response([subscription_data(subscription, request) for subscription in subscriptions])


class SubscriptionActionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _subscription(self, request, pk, **filters):
        return get_object_or_404(
            Subscription.objects.select_related('creator', 'tier'),
            pk=pk, subscriber=request.user, status=Subscription.Status.ACTIVE, **filters,
        )

    def post(self, request, pk, action):
        if action == 'cancel':
            subscription = self._subscription(request, pk)
            if not subscription.cancel_at_period_end:
                services.cancel_subscription(subscription)
            return Response(subscription_data(subscription, request))
        if action == 'renew':
            subscription = self._subscription(request, pk, cancel_at_period_end=True)
            services.renew_subscription(subscription)
            return Response(subscription_data(subscription, request))
        return Response({'detail': 'Unknown subscription action.'}, status=400)
