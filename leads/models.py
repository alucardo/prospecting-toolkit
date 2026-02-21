from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class City(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class SearchQuery(models.Model):
    SOURCE_GOOGLE_MAPS = 'google_maps'
    SOURCE_UBER_EATS = 'uber_eats'

    SOURCE_CHOICES = [
        (SOURCE_GOOGLE_MAPS, 'Google Maps'),
        (SOURCE_UBER_EATS, 'Uber Eats'),
    ]

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='search_queries')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default=SOURCE_GOOGLE_MAPS)
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
    STATUS_CLIENT = 'client'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Nowy'),
        (STATUS_NO_ANSWER, 'Nie odebrano'),
        (STATUS_TALKED, 'Odebrano - rozmowa'),
        (STATUS_CALL_LATER, 'Zadzwonić później'),
        (STATUS_NOT_INTERESTED, 'Nie zainteresowany'),
        (STATUS_INTERESTED, 'Zainteresowany'),
        (STATUS_CLIENT, 'Klient'),
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

    analysis_url = models.URLField(max_length=500, blank=True)
    cold_email_sent = models.BooleanField(default=False)
    email_scraped = models.BooleanField(default=False)

    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

class CallLog(models.Model):
    TYPE_CALL = 'call'
    TYPE_EMAIL = 'email'

    TYPE_CHOICES = [
        (TYPE_CALL, 'Telefon'),
        (TYPE_EMAIL, 'Email'),
    ]

    STATUS_NO_ANSWER = 'no_answer'
    STATUS_TALKED = 'talked'
    STATUS_CALL_LATER = 'call_later'
    STATUS_NOT_INTERESTED = 'not_interested'
    STATUS_INTERESTED = 'interested'
    STATUS_EMAIL_SENT = 'email_sent'

    STATUS_CHOICES = [
        (STATUS_NO_ANSWER, 'Nie odebrano'),
        (STATUS_TALKED, 'Odebrano - rozmowa'),
        (STATUS_CALL_LATER, 'Zadzwonić później'),
        (STATUS_NOT_INTERESTED, 'Nie zainteresowany'),
        (STATUS_INTERESTED, 'Zainteresowany'),
        (STATUS_EMAIL_SENT, 'Wysłano email'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='call_logs'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='call_logs'
    )
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default=TYPE_CALL)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    note = models.TextField(blank=True)
    next_contact_date = models.DateField(null=True, blank=True)
    is_reminder_active = models.BooleanField(default=False)
    called_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.name} — {self.get_status_display()} ({self.called_at|date:'d.m.Y'})"


class GoogleBusinessAnalysis(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='business_analyses')
    raw_data = models.JSONField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    reviews_count = models.IntegerField(null=True, blank=True)
    has_description = models.BooleanField(default=False)
    has_website = models.BooleanField(default=False)
    has_phone = models.BooleanField(default=False)
    has_hours = models.BooleanField(default=False)
    photos_count = models.IntegerField(null=True, blank=True)
    categories = models.JSONField(null=True, blank=True)
    ai_summary = models.TextField(blank=True)
    issues = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Analiza wizytówki {self.lead.name} ({self.created_at:%d.%m.%Y})"


class LeadContact(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=255, blank=True)
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.lead.name})"


class LeadStatusHistory(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='status_history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='status_changes')
    status = models.CharField(max_length=50)
    changed_at = models.DateTimeField(auto_now_add=True)

    def get_status_display(self):
        return dict(Lead.STATUS_CHOICES).get(self.status, self.status)

    def __str__(self):
        return f"{self.lead.name} → {self.status} ({self.changed_at})"


class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notatka do {self.lead.name} ({self.created_at})"


class ImportFile(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='import_files')
    file = models.FileField(upload_to='imports/')
    original_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_filename} ({self.city})"


class AppSettings(models.Model):
    """Singleton — zawsze tylko jeden rekord."""
    openai_api_key = models.CharField(max_length=255, blank=True)
    dataforseo_login = models.CharField(max_length=255, blank=True)
    dataforseo_password = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Ustawienia aplikacji'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Ustawienia aplikacji'