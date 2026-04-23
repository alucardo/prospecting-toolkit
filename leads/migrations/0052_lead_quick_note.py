from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0051_city_assigned_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='quick_note',
            field=models.CharField(
                max_length=500,
                blank=True,
                verbose_name='Szybka notatka',
            ),
        ),
    ]
