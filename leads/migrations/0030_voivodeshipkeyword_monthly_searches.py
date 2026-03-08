from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0029_voivodeshipkeyword'),
    ]

    operations = [
        migrations.AddField(
            model_name='voivodeshipkeyword',
            name='monthly_searches',
            field=models.IntegerField(blank=True, null=True, verbose_name='Wyszukania/miesiąc'),
        ),
        migrations.AddField(
            model_name='voivodeshipkeyword',
            name='searches_updated_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Data aktualizacji'),
        ),
    ]
