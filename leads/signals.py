from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LeadKeyword, VoivodeshipKeyword


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
