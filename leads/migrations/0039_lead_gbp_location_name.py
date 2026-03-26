from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0038_appsettings_google_refresh_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='gbp_location_name',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='GBP location name',
                help_text='Format: locations/123456789',
            ),
        ),
    ]
