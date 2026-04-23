from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0050_leadtask_assigned_to'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='assigned_to',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_cities',
                to='auth.user',
                verbose_name='Przypisany handlowiec',
            ),
        ),
    ]
