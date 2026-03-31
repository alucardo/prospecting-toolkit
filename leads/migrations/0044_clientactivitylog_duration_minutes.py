from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0043_gbpmetricssnapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientactivitylog',
            name='duration_minutes',
            field=models.IntegerField(
                null=True,
                blank=True,
                verbose_name='Czas trwania',
                help_text='Czas w minutach (co 15 min, od 15 do 360)',
            ),
        ),
    ]
