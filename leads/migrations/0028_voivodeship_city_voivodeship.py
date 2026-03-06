from django.db import migrations, models
import django.db.models.deletion


VOIVODESHIPS = [
    ('Dolnośląskie',            'Lower Silesian Voivodeship, Poland'),
    ('Kujawsko-Pomorskie',      'Kuyavian-Pomeranian Voivodeship, Poland'),
    ('Lubelskie',               'Lublin Voivodeship, Poland'),
    ('Lubuskie',                'Lubusz Voivodeship, Poland'),
    ('Łódzkie',                 'Lodz Voivodeship, Poland'),
    ('Małopolskie',             'Lesser Poland Voivodeship, Poland'),
    ('Mazowieckie',             'Masovian Voivodeship, Poland'),
    ('Opolskie',                'Opole Voivodeship, Poland'),
    ('Podkarpackie',            'Subcarpathian Voivodeship, Poland'),
    ('Podlaskie',               'Podlaskie Voivodeship, Poland'),
    ('Pomorskie',               'Pomeranian Voivodeship, Poland'),
    ('Śląskie',                 'Silesian Voivodeship, Poland'),
    ('Świętokrzyskie',          'Holy Cross Voivodeship, Poland'),
    ('Warmińsko-Mazurskie',     'Warmian-Masurian Voivodeship, Poland'),
    ('Wielkopolskie',           'Greater Poland Voivodeship, Poland'),
    ('Zachodniopomorskie',      'West Pomeranian Voivodeship, Poland'),
]


def seed_voivodeships(apps, schema_editor):
    Voivodeship = apps.get_model('leads', 'Voivodeship')
    for name, dataforseo_name in VOIVODESHIPS:
        Voivodeship.objects.get_or_create(
            name=name,
            defaults={'dataforseo_name': dataforseo_name},
        )


def unseed_voivodeships(apps, schema_editor):
    Voivodeship = apps.get_model('leads', 'Voivodeship')
    Voivodeship.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0027_pipeline_show_on_dashboard'),
    ]

    operations = [
        # 1. Utwórz tabelę Voivodeship
        migrations.CreateModel(
            name='Voivodeship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('dataforseo_name', models.CharField(max_length=150)),
            ],
            options={
                'verbose_name': 'Województwo',
                'verbose_name_plural': 'Województwa',
                'ordering': ['name'],
            },
        ),
        # 2. Wypełnij danymi
        migrations.RunPython(seed_voivodeships, unseed_voivodeships),
        # 3. Dodaj FK do City
        migrations.AddField(
            model_name='city',
            name='voivodeship',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cities',
                to='leads.voivodeship',
                verbose_name='Województwo',
            ),
        ),
    ]
