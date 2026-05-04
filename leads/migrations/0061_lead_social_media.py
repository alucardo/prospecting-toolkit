from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0060_postidea'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='social_instagram',
            field=models.URLField(blank=True, verbose_name='Instagram'),
        ),
        migrations.AddField(
            model_name='lead',
            name='social_facebook',
            field=models.URLField(blank=True, verbose_name='Facebook'),
        ),
        migrations.AddField(
            model_name='lead',
            name='social_tiktok',
            field=models.URLField(blank=True, verbose_name='TikTok'),
        ),
        migrations.AddField(
            model_name='lead',
            name='social_youtube',
            field=models.URLField(blank=True, verbose_name='YouTube'),
        ),
    ]
