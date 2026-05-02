from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0056_brandprofile_extra_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='gbpmetricssnapshot',
            name='conversations',
            field=models.IntegerField(null=True, blank=True, verbose_name='Wiadomości (konwersacje)'),
        ),
        migrations.AddField(
            model_name='gbpmetricssnapshot',
            name='bookings',
            field=models.IntegerField(null=True, blank=True, verbose_name='Rezerwacje'),
        ),
        migrations.AddField(
            model_name='gbpmetricssnapshot',
            name='food_orders',
            field=models.IntegerField(null=True, blank=True, verbose_name='Zamówienia jedzenia'),
        ),
        migrations.AddField(
            model_name='gbpmetricssnapshot',
            name='food_menu_clicks',
            field=models.IntegerField(null=True, blank=True, verbose_name='Kliknięcia w menu'),
        ),
    ]
