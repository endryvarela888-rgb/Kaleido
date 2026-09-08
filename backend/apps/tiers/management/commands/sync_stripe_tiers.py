from django.core.management.base import BaseCommand

from apps.tiers.models import Tier
from apps.tiers.services import sync_tier_to_stripe


class Command(BaseCommand):
    help = 'Creates the Stripe Product+Price for every tier missing one.'

    def handle(self, *args, **options):
        pending = Tier.objects.filter(stripe_price_id='')
        for tier in pending:
            sync_tier_to_stripe(tier)
            self.stdout.write(f'Synced: {tier}')
        self.stdout.write(self.style.SUCCESS(f'Synced {pending.count()} tier(s).'))