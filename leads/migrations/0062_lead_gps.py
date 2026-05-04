from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0061_lead_social_media'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='latitude',
            field=models.FloatField(null=True, blank=True, verbose_name='Szerokość geograficzna'),
        ),
        migrations.AddField(
            model_name='lead',
            name='longitude',
            field=models.FloatField(null=True, blank=True, verbose_name='Długość geograficzna'),
        ),
    ]
