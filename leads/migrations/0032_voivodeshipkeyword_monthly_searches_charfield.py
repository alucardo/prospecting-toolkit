from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0031_googlebusinessanalysis_show_keyword_searches'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voivodeshipkeyword',
            name='monthly_searches',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Wyszukania/miesiąc'),
        ),
    ]
