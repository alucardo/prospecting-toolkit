from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0028_voivodeship_city_voivodeship'),
    ]

    operations = [
        migrations.CreateModel(
            name='VoivodeshipKeyword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phrase', models.CharField(max_length=200)),
                ('voivodeship', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='keywords',
                    to='leads.voivodeship',
                )),
            ],
            options={
                'ordering': ['phrase'],
                'unique_together': {('voivodeship', 'phrase')},
            },
        ),
    ]
