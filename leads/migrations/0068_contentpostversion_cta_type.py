from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0067_contentpost_external_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentpostversion',
            name='cta_type',
            field=models.CharField(
                max_length=20,
                blank=True,
                verbose_name='Typ przycisku CTA',
                choices=[
                    ('LEARN_MORE', 'Dowiedz się więcej'),
                    ('BOOK', 'Zarezerwuj'),
                    ('ORDER', 'Zamów online'),
                    ('SHOP', 'Kup teraz'),
                    ('SIGN_UP', 'Zarejestruj się'),
                    ('CALL', 'Zadzwoń'),
                ],
            ),
        ),
    ]
