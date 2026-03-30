from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0041_leadnapentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeadTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='Zadanie')),
                ('is_done', models.BooleanField(default=False, verbose_name='Wykonane')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('done_at', models.DateTimeField(null=True, blank=True)),
                ('lead', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tasks',
                    to='leads.lead',
                    verbose_name='Lead',
                )),
            ],
            options={
                'verbose_name': 'Zadanie',
                'verbose_name_plural': 'Zadania',
                'ordering': ['is_done', '-created_at'],
            },
        ),
    ]
