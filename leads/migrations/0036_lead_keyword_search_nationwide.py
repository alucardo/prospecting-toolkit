from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0035_googlebusinessanalysis_show_price_list'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='keyword_search_nationwide',
            field=models.BooleanField(default=False),
        ),
    ]
