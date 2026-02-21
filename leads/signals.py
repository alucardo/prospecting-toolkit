from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CallLog


@receiver(post_save, sender=CallLog)
def update_lead_status(sender, instance, created, **kwargs):
    if not created:
        return

    lead = instance.lead

    # Dezaktywuj poprzednie przypomnienia jeśli nowy kontakt jest skuteczny
    if instance.status != 'no_answer':
        CallLog.objects.filter(
            lead=lead,
            is_reminder_active=True
        ).exclude(pk=instance.pk).update(is_reminder_active=False)

    # Aktywuj przypomnienie dla nowego kontaktu jeśli ma datę
    if instance.next_contact_date:
        instance.is_reminder_active = True
        instance.save()

    # Aktualizuj status leada
    STATUS_MAP = {
        'no_answer': 'no_answer',
        'talked': 'talked',
        'call_later': 'call_later',
        'not_interested': 'not_interested',
        'interested': 'interested',
        'email_sent': 'call_later',
    }

    new_status = STATUS_MAP.get(instance.status)
    if new_status:
        lead.status = new_status
        lead.save()
