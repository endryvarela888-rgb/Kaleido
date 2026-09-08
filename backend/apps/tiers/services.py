import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def sync_tier_to_stripe(tier):
    """
    Creates the Stripe Product/Price on first save. Since Stripe Prices are
    immutable, an edit to `price` creates a *new* Price and archives the
    old one — the Tier keeps pointing to whichever Price is current.
    """
    if not tier.stripe_product_id:
        product = stripe.Product.create(
            name=f'{tier.creator.display_name} — {tier.name}',
            metadata={'tier_id': tier.id},
        )
        tier.stripe_product_id = product.id
    else:
        stripe.Product.modify(tier.stripe_product_id, name=f'{tier.creator.display_name} — {tier.name}')

    old_price_id = tier.stripe_price_id
    price = stripe.Price.create(
        product=tier.stripe_product_id,
        unit_amount=int(tier.price * 100),
        currency='usd',
        recurring={'interval': 'month'},
    )
    tier.stripe_price_id = price.id
    tier.save(update_fields=['stripe_product_id', 'stripe_price_id'])

    if old_price_id and old_price_id != price.id:
        stripe.Price.modify(old_price_id, active=False)