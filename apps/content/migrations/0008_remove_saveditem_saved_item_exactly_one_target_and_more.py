from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0007_saveditem'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='saveditem',
            name='unique_saved_content_per_user',
        ),
        migrations.RemoveConstraint(
            model_name='saveditem',
            name='unique_saved_collection_per_user',
        ),
        migrations.RemoveConstraint(
            model_name='saveditem',
            name='saved_item_exactly_one_target',
        ),
        migrations.AddConstraint(
            model_name='saveditem',
            constraint=models.UniqueConstraint(
                condition=models.Q(content__isnull=False),
                fields=('user', 'content'),
                name='unique_saved_content_per_user',
            ),
        ),
        migrations.AddConstraint(
            model_name='saveditem',
            constraint=models.UniqueConstraint(
                condition=models.Q(collection__isnull=False),
                fields=('user', 'collection'),
                name='unique_saved_collection_per_user',
            ),
        ),
        migrations.AddConstraint(
            model_name='saveditem',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(content__isnull=False, collection__isnull=True)
                    | models.Q(content__isnull=True, collection__isnull=False)
                ),
                name='saved_item_exactly_one_target',
            ),
        ),
    ]
