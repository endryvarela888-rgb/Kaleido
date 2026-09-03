from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0008_remove_saveditem_saved_item_exactly_one_target_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_viewed_at', models.DateTimeField(auto_now=True)),
                ('progress_seconds', models.FloatField(default=0)),
                ('duration_seconds', models.FloatField(blank=True, null=True)),
                ('completed', models.BooleanField(default=False)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history_entries', to='content.content')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_history', to='users.user')),
            ],
            options={
                'ordering': ['-last_viewed_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='contenthistory',
            constraint=models.UniqueConstraint(fields=('user', 'content'), name='unique_content_history_per_user'),
        ),
    ]
