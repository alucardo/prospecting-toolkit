from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0062_lead_gps'),
    ]

    operations = [
        migrations.AddField(
            model_name='appsettings',
            name='google_maps_api_key',
            field=models.CharField(max_length=255, blank=True, verbose_name='Google Maps API Key (Geocoding)'),
        ),
    ]
