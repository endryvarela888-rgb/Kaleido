from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0006_contentlike_comment'),
    ]

    operations = [
        migrations.CreateModel(
            name='SavedItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('collection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to='content.collection')),
                ('content', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='saved_by', to='content.content')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddConstraint(
            model_name='saveditem',
            constraint=models.UniqueConstraint(condition=models.Q(('content__isnull', False)), fields=('user', 'content'), name='unique_saved_content_per_user'),
        ),
        migrations.AddConstraint(
            model_name='saveditem',
            constraint=models.UniqueConstraint(condition=models.Q(('collection__isnull', False)), fields=('user', 'collection'), name='unique_saved_collection_per_user'),
        ),
        migrations.AddConstraint(
            model_name='saveditem',
            constraint=models.CheckConstraint(condition=models.Q(('content__isnull', False), ('collection__isnull', True)) | models.Q(('content__isnull', True), ('collection__isnull', False)), name='saved_item_exactly_one_target'),
        ),
    ]
