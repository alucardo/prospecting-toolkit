from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0059_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostIdeaCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True, verbose_name='Nazwa kategorii')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Kategoria pomysłów',
                'verbose_name_plural': 'Kategorie pomysłów',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PostIdea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Tytuł pomysłu')),
                ('hint', models.TextField(blank=True, verbose_name='Wskazówka dla AI', help_text='Opcjonalny opis który trafi do promptu AI — co podkreślić, na co zwrócić uwagę')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ideas',
                    to='leads.postideacategory',
                    verbose_name='Kategoria',
                )),
            ],
            options={
                'verbose_name': 'Pomysł na post',
                'verbose_name_plural': 'Pomysły na posty',
                'ordering': ['title'],
            },
        ),
    ]
