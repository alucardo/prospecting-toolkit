from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0047_appsettings_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientactivitylog',
            name='is_highlighted',
            field=models.BooleanField(default=False, verbose_name='Wyróżniony'),
        ),
    ]
