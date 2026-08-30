import stripe
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.users.decorators import creator_required

from .forms import TierForm
from .models import Tier
from .services import sync_tier_to_stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

MAX_TIERS_PER_CREATOR = 3


@creator_required
def creator_tier_list(request):
    tiers = request.user.tiers.filter(is_active=True).order_by('level')

    if request.method == 'POST':
        if tiers.count() >= MAX_TIERS_PER_CREATOR:
            messages.error(request, f'You can only have up to {MAX_TIERS_PER_CREATOR} active tiers.')
            return redirect('creator_tiers:list')

        form = TierForm(request.POST, creator=request.user)
        if form.is_valid():
            tier = form.save(commit=False)
            tier.creator = request.user
            tier.save()
            sync_tier_to_stripe(tier)
            messages.success(request, 'Tier created.')
            return redirect('creator_tiers:list')
    else:
        form = TierForm(creator=request.user)

    return render(request, 'creator_dashboard/tier_list.html', {
        'form': form, 'tiers': tiers,
        'can_add_tier': tiers.count() < MAX_TIERS_PER_CREATOR,
        'active_tab': 'tiers',
    })


@creator_required
def creator_tier_edit(request, pk):
    tier = get_object_or_404(Tier, pk=pk, creator=request.user)
    if request.method == 'POST':
        form = TierForm(request.POST, instance=tier, creator=request.user)
        if form.is_valid():
            tier = form.save()
            sync_tier_to_stripe(tier)
            messages.success(request, 'Tier updated.')
            return redirect('creator_tiers:list')
    else:
        form = TierForm(instance=tier, creator=request.user)
    return render(request, 'creator_dashboard/tier_edit.html', {'form': form, 'tier': tier, 'active_tab': 'tiers'})
@creator_required
@require_POST
def creator_tier_deactivate(request, pk):
    tier = get_object_or_404(Tier, pk=pk, creator=request.user)
    tier.is_active = False
    tier.save(update_fields=['is_active'])
    if tier.stripe_price_id:
        stripe.Price.modify(tier.stripe_price_id, active=False)
    messages.success(request, 'Tier deactivated. Existing subscribers keep access; no new signups.')
    return redirect('creator_tiers:list')