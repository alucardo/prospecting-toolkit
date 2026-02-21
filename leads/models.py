from django.db import models

# Create your models here.
class City(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class SearchQuery(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='search_queries')
    keyword = models.CharField(max_length=255)
    limit = models.IntegerField(default=100)
    apify_run_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.keyword} - {self.city} ({self.status})"


class Lead(models.Model):
    STATUS_NEW = 'new'
    STATUS_NO_ANSWER = 'no_answer'
    STATUS_TALKED = 'talked'
    STATUS_CALL_LATER = 'call_later'
    STATUS_NOT_INTERESTED = 'not_interested'
    STATUS_INTERESTED = 'interested'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Nowy'),
        (STATUS_NO_ANSWER, 'Nie odebrano'),
        (STATUS_TALKED, 'Odebrano - rozmowa'),
        (STATUS_CALL_LATER, 'Zadzwonić później'),
        (STATUS_NOT_INTERESTED, 'Nie zainteresowany'),
        (STATUS_INTERESTED, 'Zainteresowany'),
        (STATUS_REJECTED, 'Odrzucony'),
    ]

    SOURCE_GOOGLE_MAPS = 'google_maps'
    SOURCE_FILE = 'file'
    SOURCE_REFERRAL = 'referral'
    SOURCE_CHOICES = [
        (SOURCE_GOOGLE_MAPS, 'Google Maps'),
        (SOURCE_FILE, 'Plik'),
        (SOURCE_REFERRAL, 'Polecenie'),
    ]

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='leads')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default=SOURCE_GOOGLE_MAPS)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_NEW)

    name = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=500, blank=True)
    email = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=500, blank=True)

    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

class CallLog(models.Model):
    STATUS_NO_ANSWER = 'no_answer'
    STATUS_TALKED = 'talked'
    STATUS_CALL_LATER = 'call_later'
    STATUS_NOT_INTERESTED = 'not_interested'
    STATUS_INTERESTED = 'interested'

    STATUS_CHOICES = [
        (STATUS_NO_ANSWER, 'Nie odebrano'),
        (STATUS_TALKED, 'Odebrano - rozmowa'),
        (STATUS_CALL_LATER, 'Zadzwonić później'),
        (STATUS_NOT_INTERESTED, 'Nie zainteresowany'),
        (STATUS_INTERESTED, 'Zainteresowany'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='call_logs'
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    note = models.TextField(blank=True)
    next_contact_date = models.DateField(null=True, blank=True)
    called_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.name} — {self.get_status_display()} ({self.called_at|date:'d.m.Y'})"