from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CallLog, LeadStatusHistory, LeadKeyword, VoivodeshipKeyword


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
        CallLog.objects.filter(pk=instance.pk).update(is_reminder_active=True)

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
    if new_status and lead.status != new_status:
        LeadStatusHistory.objects.create(
            lead=lead,
            user=instance.user,
            status=new_status,
        )
        lead.status = new_status
        lead.save()


@receiver(post_save, sender=LeadKeyword)
def sync_keyword_to_voivodeship(sender, instance, created, **kwargs):
    """
    Po dodaniu frazy kluczowej do leada automatycznie synkuje ją
    do tabeli VoivodeshipKeyword (jeśli lead ma miasto z województwem).
    Istniejące frazy są ignorowane (get_or_create).
    """
    try:
        voivodeship = instance.lead.city.voivodeship
    except AttributeError:
        return  # lead nie ma miasta lub miasto nie ma województwa

    if voivodeship is None:
        return

    VoivodeshipKeyword.objects.get_or_create(
        voivodeship=voivodeship,
        phrase=instance.phrase,
    )
