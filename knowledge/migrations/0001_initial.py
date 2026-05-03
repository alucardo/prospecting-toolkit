from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='KnowledgeTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nazwa')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tagi',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='VideoInspiration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Tytuł')),
                ('drive_url', models.URLField(verbose_name='Link do Google Drive')),
                ('description', models.TextField(blank=True, verbose_name='Opis / przemyślenia')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tags', models.ManyToManyField(
                    blank=True,
                    related_name='videos',
                    to='knowledge.knowledgetag',
                    verbose_name='Tagi',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='video_inspirations',
                    to='auth.user',
                    verbose_name='Dodano przez',
                )),
            ],
            options={
                'verbose_name': 'Inspiracja wideo',
                'verbose_name_plural': 'Inspiracje wideo',
                'ordering': ['-created_at'],
            },
        ),
    ]
