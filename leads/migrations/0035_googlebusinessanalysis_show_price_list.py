from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0034_callscript'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlebusinessanalysis',
            name='show_price_list',
            field=models.BooleanField(default=False),
        ),
    ]
