from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0042_leadtask'),
    ]

    operations = [
        migrations.CreateModel(
            name='GBPMetricsSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(verbose_name='Rok')),
                ('month', models.IntegerField(verbose_name='Miesiąc')),
                ('day', models.IntegerField(null=True, blank=True, verbose_name='Dzień')),
                ('calls', models.IntegerField(null=True, blank=True, verbose_name='Telefony')),
                ('profile_views', models.IntegerField(null=True, blank=True, verbose_name='Wyświetlenia profilu')),
                ('direction_requests', models.IntegerField(null=True, blank=True, verbose_name='Zapytania o trasę')),
                ('website_visits', models.IntegerField(null=True, blank=True, verbose_name='Odwiedziny witryny')),
                ('source', models.CharField(
                    max_length=10,
                    choices=[('manual', 'Ręcznie'), ('api', 'API')],
                    default='manual',
                    verbose_name='Źródło',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lead', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='gbp_metrics',
                    to='leads.lead',
                    verbose_name='Klient',
                )),
            ],
            options={
                'verbose_name': 'Metryki GBP',
                'verbose_name_plural': 'Metryki GBP',
                'ordering': ['-year', '-month', '-day'],
                'unique_together': {('lead', 'year', 'month', 'day', 'source')},
            },
        ),
    ]
