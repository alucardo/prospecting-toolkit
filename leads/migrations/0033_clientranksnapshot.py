from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0032_voivodeshipkeyword_monthly_searches_charfield'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientRankSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('positions', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('triggered_by', models.CharField(
                    choices=[('auto', 'Automatyczny'), ('manual', 'Ręczny')],
                    default='auto',
                    max_length=20,
                )),
                ('lead', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='rank_snapshots',
                    to='leads.lead',
                )),
            ],
            options={
                'ordering': ['-year', '-month'],
                'unique_together': {('lead', 'year', 'month')},
            },
        ),
    ]
