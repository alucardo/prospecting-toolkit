from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0049_pipeline_is_default'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='leadtask',
            name='assigned_to',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_tasks',
                to='auth.user',
                verbose_name='Przypisany do',
            ),
        ),
    ]
