from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0045_taskblueprint_taskblueprintitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadtask',
            name='due_date_start',
            field=models.DateField(null=True, blank=True, verbose_name='Termin od'),
        ),
        migrations.AddField(
            model_name='leadtask',
            name='due_date_end',
            field=models.DateField(null=True, blank=True, verbose_name='Termin do'),
        ),
    ]
