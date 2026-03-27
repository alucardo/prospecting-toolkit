from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0040_napdirectorytag_napdirectory'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeadNapEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    max_length=20,
                    choices=[
                        ('added_by_us', 'Dodany przeze mnie'),
                        ('pre_existing', 'Był przed nami'),
                    ],
                    verbose_name='Status wpisu',
                )),
                ('notes', models.CharField(max_length=500, blank=True, verbose_name='Notatka')),
                ('added_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True,
                    to='auth.user',
                    related_name='nap_entries',
                    verbose_name='Oznaczył',
                )),
                ('directory', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='leads.napdirectory',
                    related_name='lead_entries',
                    verbose_name='Katalog NAP',
                )),
                ('lead', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='leads.lead',
                    related_name='nap_entries',
                    verbose_name='Klient',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Wpis NAP klienta',
                'verbose_name_plural': 'Wpisy NAP klientów',
                'ordering': ['directory__name'],
                'unique_together': {('lead', 'directory')},
            },
        ),
    ]
