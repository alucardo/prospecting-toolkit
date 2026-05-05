from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0063_appsettings_google_maps_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandprofile',
            name='colors',
            field=models.JSONField(default=list, blank=True, verbose_name='Kolory marki'),
        ),
        migrations.AddField(
            model_name='brandprofile',
            name='fonts',
            field=models.JSONField(default=list, blank=True, verbose_name='Czcionki marki'),
        ),
    ]
