from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
import random
from apps.content.queries import visible_content_filter



from .forms import (
    EmailLoginForm,
    ProfileEditForm,
    ResendActivationForm,
    SignupForm,
    StyledPasswordChangeForm,
)
from .models import CreatorProfile, User
from .tokens import account_activation_token

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from apps.subscriptions.models import Subscription
from apps.content.access import annotate_lock_state

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        existing_user = User.objects.filter(
            email__iexact=request.POST.get('email', '').strip(),
        ).first()
        if existing_user and not existing_user.is_active:
            _send_activation_email(request, existing_user)
            return render(
                request,
                'users/activation_sent.html',
                {'email': existing_user.email, 'resent': True},
            )

        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            _send_activation_email(request, user)
            return render(request, 'users/activation_sent.html', {'email': user.email})
    else:
        form = SignupForm()

    return render(request, 'users/signup.html', {'form': form})


def _send_activation_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = request.build_absolute_uri(
        reverse('users:activate', kwargs={'uidb64': uid, 'token': token})
    )
    message = render_to_string('users/activation_email.html', {
        'user': user,
        'activation_link': activation_link,
    })
    send_mail(
        subject='Confirm your Kaleido account',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def resend_activation_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = ResendActivationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email__iexact=email, is_active=False).first()
            if user:
                _send_activation_email(request, user)

            # Use the same response whether the account exists or is already
            # active so this endpoint cannot be used to enumerate accounts.
            return render(
                request,
                'users/activation_sent.html',
                {'email': email, 'resent': True},
            )
    else:
        form = ResendActivationForm()

    return render(request, 'users/resend_activation.html', {'form': form})


def activate_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save(update_fields=['is_active'])
        login(request, user)
        messages.success(request, 'Your account is verified. Welcome!')
        return redirect('core:home')

    return render(request, 'users/activation_invalid.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('core:home')
    else:
        form = EmailLoginForm(request)

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('core:home')

def profile_view(request, pk):
    profile_user = get_object_or_404(User, pk=pk)
    is_own_profile = request.user.is_authenticated and request.user.pk == profile_user.pk

    edit_form = ProfileEditForm(instance=profile_user) if is_own_profile else None

    if is_own_profile and request.method == 'POST':
        if 'save_profile' in request.POST:
            edit_form = ProfileEditForm(request.POST, request.FILES, instance=profile_user)
            if edit_form.is_valid():
                edit_form.save()
                messages.success(request, 'Profile updated.')
                return redirect('users:profile', pk=profile_user.pk)
        elif 'save_featured' in request.POST:
            featured_ids = request.POST.getlist('featured')[:6]
            profile_user.content_items.update(is_featured=False)
            profile_user.content_items.filter(id__in=featured_ids).update(is_featured=True)
            messages.success(request, 'Featured content updated.')
            return redirect('users:profile', pk=profile_user.pk)

    tiers, featured_items, library_items, all_own_content, collections = [], [], [], [], []

    if profile_user.is_creator:
        tiers = profile_user.tiers.filter(is_active=True).order_by('level')

        all_content = list(
            profile_user.content_items
            .filter(visible_content_filter())
            .select_related('minimum_tier')
            .order_by('-created_at')
        )
        annotate_lock_state(request, all_content)

        featured_items = [c for c in all_content if c.is_featured][:6]
        library_items = all_content[:]
        random.shuffle(library_items)

        if is_own_profile:
            all_own_content = all_content

        collections = (
            profile_user.collections
            .filter(visible_content_filter(prefix='items__'))
            .select_related('minimum_tier')
            .annotate(
                visible_item_count=Count(
                    'items',
                    filter=visible_content_filter(prefix='items__'),
                )
            )
            .order_by('-created_at')
        )

    my_subscription = None
    if not is_own_profile and profile_user.is_creator and request.user.is_authenticated:
        my_subscription = Subscription.objects.filter(
            subscriber=request.user, creator=profile_user, status=Subscription.Status.ACTIVE,
        ).select_related('tier').first()

    context = {
        'profile_user': profile_user,
        'is_own_profile': is_own_profile,
        'edit_form': edit_form,
        'tiers': tiers,
        'featured_items': featured_items,
        'library_items': library_items,
        'all_own_content': all_own_content,
        'collections': collections,
        'initial_library_tab': 'content' if library_items else 'collections',
        'my_subscription': my_subscription,
    }
    return render(request, 'users/profile.html', context)
@login_required
def settings_view(request):
    password_form = StyledPasswordChangeForm(user=request.user)

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                # Changing the password rotates Django's session auth hash;
                # without this, the user gets silently logged out right
                # after successfully changing their own password.
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated.')
                return redirect('users:settings')

        elif 'become_creator' in request.POST and not request.user.is_creator:
            request.user.is_creator = True
            request.user.save(update_fields=['is_creator'])
            CreatorProfile.objects.get_or_create(user=request.user)
            messages.success(request, "You're a creator now — set up your tiers from your profile.")
            return redirect('users:settings')

    return render(request, 'users/settings.html', {'password_form': password_form})
