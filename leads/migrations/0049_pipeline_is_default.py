from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0048_clientactivitylog_is_highlighted'),
    ]

    operations = [
        migrations.AddField(
            model_name='pipeline',
            name='is_default',
            field=models.BooleanField(default=False, verbose_name='Domyślny'),
        ),
    ]
