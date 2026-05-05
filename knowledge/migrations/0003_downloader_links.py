from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0002_knowledgesettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='knowledgesettings',
            name='tiktok_downloader_url',
            field=models.URLField(blank=True, verbose_name='Link do programu do pobierania TikTok'),
        ),
        migrations.AddField(
            model_name='knowledgesettings',
            name='instagram_downloader_url',
            field=models.URLField(blank=True, verbose_name='Link do programu do pobierania Instagram'),
        ),
    ]
