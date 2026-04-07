from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leads', '0046_leadtask_due_dates'),
    ]

    operations = [
        migrations.AddField(
            model_name='appsettings',
            name='smtp_host',
            field=models.CharField(max_length=255, blank=True, verbose_name='SMTP Host'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='smtp_port',
            field=models.IntegerField(default=587, verbose_name='SMTP Port'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='smtp_username',
            field=models.CharField(max_length=255, blank=True, verbose_name='SMTP Login'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='smtp_password',
            field=models.CharField(max_length=255, blank=True, verbose_name='SMTP Hasło'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='smtp_use_tls',
            field=models.BooleanField(default=True, verbose_name='SMTP TLS'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='smtp_from_email',
            field=models.CharField(max_length=255, blank=True, verbose_name='Adres nadawcy'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='imap_host',
            field=models.CharField(max_length=255, blank=True, verbose_name='IMAP Host'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='imap_port',
            field=models.IntegerField(default=993, verbose_name='IMAP Port'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='imap_username',
            field=models.CharField(max_length=255, blank=True, verbose_name='IMAP Login'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='imap_password',
            field=models.CharField(max_length=255, blank=True, verbose_name='IMAP Hasło'),
        ),
        migrations.AddField(
            model_name='appsettings',
            name='imap_use_ssl',
            field=models.BooleanField(default=True, verbose_name='IMAP SSL'),
        ),
    ]
