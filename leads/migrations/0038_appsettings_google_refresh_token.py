from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0037_clientactivitylog'),
    ]

    operations = [
        migrations.AddField(
            model_name='appsettings',
            name='google_refresh_token',
            field=models.TextField(blank=True),
        ),
    ]
