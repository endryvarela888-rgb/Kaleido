import random

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core import exceptions as django_exceptions
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.views import _send_activation_email, _send_password_reset_email  # reused as-is, no duplication
from apps.content.access import annotate_lock_state
from apps.content.models import Collection, Content
from apps.content.queries import social_queryset, visible_content_filter
from apps.subscriptions.models import Subscription
from apps.tiers.models import Tier
from apps.content.serializers import CollectionSerializer, ContentSerializer

from .models import CreatorProfile
from .serializers import CreatorSummarySerializer, SignupSerializer, UserSerializer
from .tokens import account_activation_token

User = get_user_model()


class MeView(generics.RetrieveUpdateAPIView):
    """GET returns the current user; PATCH updates profile fields (display
    name, bio, avatar). This is what React calls right after login to know
    who's signed in, and what the profile-edit form submits to."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _send_activation_email(request, user)
        return Response(
            {'detail': 'Check your email to activate your account.'},
            status=status.HTTP_201_CREATED,
        )


class DiscoverCreatorsView(APIView):
    """Random sample of creators for the home sidebar — mirrors the old
    Django-template version's `User.objects.filter(is_creator=True)...
    .order_by('?')[:6]`."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        creators = list(
            User.objects.filter(is_creator=True)
            .select_related('creator_profile', 'creator_profile__category')
        )
        sample = random.sample(creators, min(len(creators), 6))
        return Response(CreatorSummarySerializer(sample, many=True, context={'request': request}).data)


class CreatorProfileView(APIView):
    """Public creator page, replacing the Django-template profile view."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        creator = get_object_or_404(
            User.objects.select_related('creator_profile', 'creator_profile__category'),
            pk=pk,
            is_creator=True,
        )
        items = list(social_queryset(
            request,
            Content.objects.filter(visible_content_filter(), creator=creator)
            .select_related('creator', 'creator__creator_profile', 'creator__creator_profile__category', 'minimum_tier', 'collection')
            .order_by('-created_at'),
        ))
        annotate_lock_state(request, items)
        tiers = Tier.objects.filter(creator=creator, is_active=True).order_by('level')
        collections = Collection.objects.filter(creator=creator).filter(visible_content_filter(prefix='items__')).select_related(
            'creator', 'minimum_tier',
        ).annotate(item_count=Count('items', filter=visible_content_filter(prefix='items__'))).distinct().order_by('-created_at')
        subscription = None
        if request.user.is_authenticated:
            subscription = Subscription.objects.filter(
                subscriber=request.user, creator=creator, status=Subscription.Status.ACTIVE,
            ).select_related('tier').first()
        return Response({
            'creator': UserSerializer(creator, context={'request': request}).data,
            'tiers': [{'id': tier.id, 'name': tier.name, 'description': tier.description, 'price': tier.price, 'level': tier.level} for tier in tiers],
            'content': ContentSerializer(items, many=True, context={'request': request}).data,
            'collections': CollectionSerializer(collections, many=True, context={'request': request}).data,
            'subscription': {'id': subscription.id, 'tier_id': subscription.tier_id, 'cancel_at_period_end': subscription.cancel_at_period_end} if subscription else None,
        })


class BecomeCreatorView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_creator:
            request.user.is_creator = True
            request.user.save(update_fields=['is_creator'])
            CreatorProfile.objects.get_or_create(user=request.user)
        return Response(UserSerializer(request.user, context={'request': request}).data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')
        if not request.user.check_password(old_password):
            return Response({'old_password': ['Current password is incorrect.']}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, request.user)
        except django_exceptions.ValidationError as error:
            return Response({'new_password': list(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(new_password)
        request.user.save(update_fields=['password'])
        return Response({'detail': 'Password updated. Please log in again.'})


def _user_from_uid(uidb64):
    """Shared decode step for activation and password-reset confirmation:
    turns the base64 uid from the emailed link back into a User, or None
    if it's malformed/unknown. Token validity is checked separately by
    each caller, since they use different token generators."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


class ResendActivationView(APIView):
    """Always answers the same way whether or not the account exists (or
    is already active) so this endpoint can't be used to enumerate
    registered emails."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        user = User.objects.filter(email__iexact=email, is_active=False).first()
        if user:
            _send_activation_email(request, user)
        return Response({'detail': 'If that account exists and needs activation, we sent a new link.'})


class ActivateAccountView(APIView):
    """Confirms the emailed token and, since there's no Django session to
    fall back on here, logs the user straight in by handing back a JWT
    pair — mirrors what the old template view did with `login(request, user)`,
    just for token auth instead of cookies."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = _user_from_uid(request.data.get('uid', ''))
        token = request.data.get('token', '')
        if user is None or not account_activation_token.check_token(user, token):
            return Response({'detail': 'This activation link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user, context={'request': request}).data,
        })


class PasswordResetRequestView(APIView):
    """Same anti-enumeration shape as ResendActivationView: the response
    never reveals whether the email is registered."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            _send_password_reset_email(user)
        return Response({'detail': 'If that email is registered, we sent a reset link.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = _user_from_uid(request.data.get('uid', ''))
        token = request.data.get('token', '')
        new_password = request.data.get('new_password', '')
        if user is None or not default_token_generator.check_token(user, token):
            return Response({'detail': 'This reset link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, user)
        except django_exceptions.ValidationError as error:
            return Response({'new_password': list(error.messages)}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({'detail': 'Password updated. You can now log in.'})