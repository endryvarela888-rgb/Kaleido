from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .models import Subscription


@login_required
def my_subscriptions(request):
    subscriptions = (
        Subscription.objects
        .filter(subscriber=request.user, status=Subscription.Status.ACTIVE)
        .select_related('creator', 'tier')
        .order_by('current_period_end')
    )
    return render(request, 'subscriptions/list.html', {'subscriptions': subscriptions})


@login_required
@require_POST
def cancel_subscription(request, subscription_id):
    subscription = get_object_or_404(
        Subscription,
        pk=subscription_id,
        subscriber=request.user,
        status=Subscription.Status.ACTIVE,
    )

    if subscription.cancel_at_period_end:
        messages.info(request, 'This subscription is already scheduled to cancel.')
        return redirect('subscriptions:my_subscriptions')

    services.cancel_subscription(subscription)
    messages.success(
        request,
        f'Your subscription to {subscription.creator.display_name} will end on '
        f'{subscription.current_period_end:%B %d, %Y}. You keep access until then.',
    )
    return redirect('subscriptions:my_subscriptions')

@login_required
@require_POST
def renew_subscription(request, subscription_id):
    subscription = get_object_or_404(
        Subscription,
        pk=subscription_id,
        subscriber=request.user,
        status=Subscription.Status.ACTIVE,
        cancel_at_period_end=True,
    )
    services.renew_subscription(subscription)
    messages.success(request, f'Your subscription to {subscription.creator.display_name} will continue.')
    return redirect('subscriptions:my_subscriptions')