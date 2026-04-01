from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0044_clientactivitylog_duration_minutes'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskBlueprint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nazwa szablonu')),
                ('description', models.TextField(blank=True, verbose_name='Opis')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Szablon zadań',
                'verbose_name_plural': 'Szablony zadań',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='TaskBlueprintItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='Treść zadania')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Kolejność')),
                ('blueprint', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='items',
                    to='leads.taskblueprint',
                    verbose_name='Szablon',
                )),
            ],
            options={
                'verbose_name': 'Pozycja szablonu',
                'verbose_name_plural': 'Pozycje szablonu',
                'ordering': ['order', 'id'],
            },
        ),
    ]
