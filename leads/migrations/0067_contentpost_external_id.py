from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0066_taskcomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentpost',
            name='external_id',
            field=models.CharField(
                max_length=500,
                blank=True,
                verbose_name='ID zewnętrzne',
                help_text='ID posta na zewnętrznej platformie (np. GBP localPosts/XXXX, w przyszłości IG, FB itd.)',
            ),
        ),
    ]
