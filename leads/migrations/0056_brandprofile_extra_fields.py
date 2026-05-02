from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0055_brandprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandprofile',
            name='description',
            field=models.TextField(blank=True, verbose_name='Opis marki'),
        ),
        migrations.AddField(
            model_name='brandprofile',
            name='usp',
            field=models.TextField(blank=True, verbose_name='USP (unikalna propozycja wartości)'),
        ),
        migrations.AddField(
            model_name='brandprofile',
            name='competition',
            field=models.TextField(blank=True, verbose_name='Konkurencja'),
        ),
        migrations.AddField(
            model_name='brandprofile',
            name='seasonality',
            field=models.TextField(blank=True, verbose_name='Sezonowość / ważne daty'),
        ),
    ]
