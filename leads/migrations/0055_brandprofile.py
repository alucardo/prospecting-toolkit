from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0054_contentpost'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrandProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tone_of_voice', models.TextField(blank=True, verbose_name='Ton komunikacji')),
                ('target_audience', models.TextField(blank=True, verbose_name='Grupa docelowa')),
                ('brand_values', models.TextField(blank=True, verbose_name='Wartości marki')),
                ('language_rules', models.TextField(blank=True, verbose_name='Zasady językowe')),
                ('keywords', models.TextField(blank=True, verbose_name='Słowa kluczowe / frazy marki')),
                ('avoid', models.TextField(blank=True, verbose_name='Czego unikać')),
                ('extra_notes', models.TextField(blank=True, verbose_name='Dodatkowe notatki')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lead', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='brand_profile',
                    to='leads.lead',
                    verbose_name='Klient',
                )),
            ],
            options={
                'verbose_name': 'Brief marki',
                'verbose_name_plural': 'Briefy marek',
            },
        ),
    ]
