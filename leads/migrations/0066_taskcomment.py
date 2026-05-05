from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0065_appsettings_unread_emails'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(verbose_name='Treść')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='leads.leadtask',
                    verbose_name='Zadanie',
                )),
                ('author', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='task_comments',
                    to='auth.user',
                    verbose_name='Autor',
                )),
                ('parent', models.ForeignKey(
                    null=True,
                    blank=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='replies',
                    to='leads.taskcomment',
                    verbose_name='Odpowiedź na',
                )),
            ],
            options={
                'verbose_name': 'Komentarz do zadania',
                'verbose_name_plural': 'Komentarze do zadań',
                'ordering': ['created_at'],
            },
        ),
    ]
