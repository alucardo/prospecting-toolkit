from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0052_lead_quick_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeadCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nazwa')),
                ('color', models.CharField(max_length=7, default='#6366f1', verbose_name='Kolor')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Kategoria leada',
                'verbose_name_plural': 'Kategorie leadów',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='lead',
            name='categories',
            field=models.ManyToManyField(
                blank=True,
                related_name='leads',
                to='leads.leadcategory',
                verbose_name='Kategorie',
            ),
        ),
    ]
