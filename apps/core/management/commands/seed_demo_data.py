import random

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from apps.content.models import Category, Content
from apps.tiers.models import Tier
from apps.tiers.services import sync_tier_to_stripe
from apps.users.models import CreatorProfile, User

fake = Faker()

CATEGORY_NAMES = ['Illustration', 'Animation', 'Music', 'Writing', 'Photography', 'Gaming']
TIER_NAMES = ['Supporter', 'Fan', 'Superfan']


class Command(BaseCommand):
    help = 'Populates the database with realistic fake data for local development/testing.'

    def add_arguments(self, parser):
        parser.add_argument('--creators', type=int, default=8)
        parser.add_argument('--content-per-creator', type=int, default=5)
        parser.add_argument('--flush', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        categories = self._create_categories()
        creators = self._create_creators(options['creators'], categories)
        self._create_tiers(creators)
        self._create_content(creators, options['content_per_creator'])

        self.stdout.write(self.style.SUCCESS(
            f'Done: {len(categories)} categories, {len(creators)} creators, '
            f'{len(creators) * 3} tiers (synced to Stripe), content generated.'
        ))

    def _flush(self):
        from apps.subscriptions.models import Subscription
        from apps.payments.models import Transaction

        Transaction.objects.all().delete()
        Subscription.objects.all().delete()
        Content.objects.all().delete()
        Tier.objects.all().delete()
        CreatorProfile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write('Existing demo data flushed.')

    def _create_categories(self):
        categories = []
        for name in CATEGORY_NAMES:
            category, _ = Category.objects.get_or_create(name=name)
            categories.append(category)
        return categories

    def _create_creators(self, count, categories):
        creators = []
        for _ in range(count):
            user = User.objects.create_user(
                email=fake.unique.email(),
                password='demopass123',
                display_name=fake.name(),
                bio=fake.sentence(nb_words=12),
                is_creator=True,
                is_active=True,
            )
            CreatorProfile.objects.create(
                user=user,
                category=random.choice(categories),
                is_verified=random.random() < 0.2,
            )
            creators.append(user)
        return creators

    def _create_tiers(self, creators):
        for creator in creators:
            # Ascending price ensures level order == price order, so the
            # hierarchy (higher level unlocks more) matches what a real
            # creator would intuitively set up.
            base_price = round(random.uniform(2, 8), 2)
            for level, name in enumerate(TIER_NAMES, start=1):
                tier = Tier.objects.create(
                    creator=creator,
                    name=name,
                    description=fake.sentence(nb_words=10),
                    price=round(base_price * level * 1.8, 2),
                    level=level,
                )
                sync_tier_to_stripe(tier)

    def _create_content(self, creators, per_creator):
        for creator in creators:
            tiers = list(creator.tiers.all())
            for _ in range(per_creator):
                content_type = random.choice(Content.ContentType.values)
                minimum_tier = random.choice([None] + tiers) if tiers else None

                Content.objects.create(
                    creator=creator,
                    content_type=content_type,
                    title=fake.sentence(nb_words=6).rstrip('.'),
                    description=fake.paragraph(nb_sentences=2),
                    minimum_tier=minimum_tier,
                    is_published=True,
                )