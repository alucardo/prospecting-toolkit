from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0030_voivodeshipkeyword_monthly_searches'),
    ]

    operations = [
        migrations.AddField(
            model_name='googlebusinessanalysis',
            name='show_keyword_searches',
            field=models.BooleanField(blank=True, default=None, null=True),
        ),
    ]
