from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0039_lead_gbp_location_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='NapDirectoryTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nazwa tagu')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Tag katalogu NAP',
                'verbose_name_plural': 'Tagi katalogów NAP',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='NapDirectory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nazwa katalogu')),
                ('url', models.URLField(max_length=500, verbose_name='Adres WWW')),
                ('is_active', models.BooleanField(default=True, verbose_name='Aktywny')),
                ('notes', models.TextField(blank=True, verbose_name='Notatki')),
                ('tags', models.ManyToManyField(
                    blank=True,
                    related_name='directories',
                    to='leads.napdirectorytag',
                    verbose_name='Tagi',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Katalog NAP',
                'verbose_name_plural': 'Katalogi NAP',
                'ordering': ['name'],
            },
        ),
    ]
