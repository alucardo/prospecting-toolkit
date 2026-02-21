from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CallLog


@receiver(post_save, sender=CallLog)
def update_lead_status(sender, instance, created, **kwargs):
    if not created:
        return

    lead = instance.lead

    # rejected ustawiamy tylko ręcznie, nie przez kontakt
    STATUS_MAP = {
        'no_answer': 'no_answer',
        'talked': 'talked',
        'call_later': 'call_later',
        'not_interested': 'not_interested',
        'interested': 'interested',
    }

    new_status = STATUS_MAP.get(instance.status)
    if new_status:
        lead.status = new_status
        lead.save()