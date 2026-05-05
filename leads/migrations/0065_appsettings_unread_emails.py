from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0064_brandprofile_colors_fonts'),
    ]

    operations = [
        migrations.AddField(
            model_name='appsettings',
            name='has_unread_emails',
            field=models.BooleanField(default=False, verbose_name='Są nieprzeczytane wiadomości'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='unread_emails_checked_at',
            field=models.DateTimeField(null=True, blank=True, verbose_name='Ostatnie sprawdzenie emaili'),
        ),
    ]
