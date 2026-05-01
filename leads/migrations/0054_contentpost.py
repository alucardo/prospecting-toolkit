from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0053_leadcategory'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(
                    max_length=50,
                    default='gbp',
                    choices=[('gbp', 'Wizytówka Google')],
                    verbose_name='Kanał',
                )),
                ('post_type', models.CharField(
                    max_length=50,
                    default='news',
                    choices=[('news', 'Aktualność')],
                    verbose_name='Typ posta',
                )),
                ('status', models.CharField(
                    max_length=50,
                    default='draft',
                    choices=[
                        ('draft', 'Szkic'),
                        ('review', 'Do zatwierdzenia'),
                        ('changes', 'Zgłoszone poprawki'),
                        ('approved', 'Zatwierdzony'),
                        ('published', 'Opublikowany'),
                    ],
                    verbose_name='Status',
                )),
                ('published_at', models.DateField(null=True, blank=True, verbose_name='Data publikacji')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lead', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='content_posts',
                    to='leads.lead',
                    verbose_name='Klient',
                )),
            ],
            options={
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posty',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContentPostVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField(default=1, verbose_name='Numer wersji')),
                ('title', models.CharField(max_length=300, blank=True, verbose_name='Tytuł')),
                ('body', models.TextField(verbose_name='Treść')),
                ('drive_url', models.URLField(blank=True, verbose_name='Link do zdjęcia (Google Drive)')),
                ('cta_text', models.CharField(max_length=100, blank=True, verbose_name='Tekst przycisku CTA')),
                ('cta_url', models.URLField(blank=True, verbose_name='URL przycisku CTA')),
                ('notes', models.TextField(blank=True, verbose_name='Notatki / uwagi do poprawek')),
                ('is_current', models.BooleanField(default=True, verbose_name='Aktualna wersja')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='versions',
                    to='leads.contentpost',
                    verbose_name='Post',
                )),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='content_versions',
                    to='auth.user',
                    verbose_name='Autor wersji',
                )),
            ],
            options={
                'verbose_name': 'Wersja posta',
                'verbose_name_plural': 'Wersje postów',
                'ordering': ['-version_number'],
            },
        ),
    ]
