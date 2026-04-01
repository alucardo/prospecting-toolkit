from django.db import models
from django.contrib.auth.models import User


class Voivodeship(models.Model):
    name = models.CharField(max_length=100, unique=True)  # np. Śląskie
    dataforseo_name = models.CharField(max_length=150)     # np. Silesian Voivodeship, Poland

    class Meta:
        ordering = ['name']
        verbose_name = 'Województwo'
        verbose_name_plural = 'Województwa'

    def __str__(self):
        return self.name


class City(models.Model):
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cities',
        verbose_name='Województwo',
    )
    name = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def has_coordinates(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def location_coordinate(self):
        """Format dla DataForSEO: lat,lng,zoom"""
        if self.has_coordinates:
            return f"{self.latitude},{self.longitude},11"
        return None


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
    STATUS_CLOSE = 'close'
    STATUS_COMPLETE_PROFILE = 'complete_profile'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Nowy'),
        (STATUS_NO_ANSWER, 'Nie odebrano'),
        (STATUS_TALKED, 'Odebrano - rozmowa'),
        (STATUS_CALL_LATER, 'Zadzwonić później'),
        (STATUS_NOT_INTERESTED, 'Nie zainteresowany'),
        (STATUS_INTERESTED, 'Zainteresowany'),
        (STATUS_CLIENT, 'Klient'),
        (STATUS_REJECTED, 'Odrzucony'),
        (STATUS_CLOSE, 'Zamknięte'),
        (STATUS_COMPLETE_PROFILE, 'Kompletny profil'),
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
    google_maps_url = models.URLField(max_length=1000, blank=True)
    keywords = models.JSONField(default=list, blank=True)
    cold_email_sent = models.BooleanField(default=False)
    email_scraped = models.BooleanField(default=False)

    raw_data = models.JSONField(default=dict)
    keyword_search_nationwide = models.BooleanField(default=False, verbose_name='Sprawdzaj pozycje dla całego kraju')
    gbp_location_name = models.CharField(
        max_length=100, blank=True,
        verbose_name='GBP location name',
        help_text='Format: locations/123456789 — identyfikator wizytyówki w Google Business Profile'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

class CallScript(models.Model):
    name = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


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
    script = models.ForeignKey(
        'CallScript',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='call_logs',
        verbose_name='Skrypt rozmowy',
    )
    note = models.TextField(blank=True)
    next_contact_date = models.DateTimeField(null=True, blank=True)
    is_reminder_active = models.BooleanField(default=False)
    called_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.name} — {self.get_status_display()} ({self.called_at|date:'d.m.Y'})"


class GoogleBusinessAnalysis(models.Model):
    STATUS_FETCHED = 'fetched'
    STATUS_ANALYZED = 'analyzed'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [
        ('pending', 'Pobieranie...'),
        ('fetched', 'Pobrano dane'),
        ('analyzed', 'Analiza gotowa'),
        ('error', 'Blad'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='business_analyses')
    raw_data = models.JSONField(null=True, blank=True)
    keywords_used = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='fetched')

    # Sekcja: Podstawowe dane
    rating = models.FloatField(null=True, blank=True)
    reviews_count = models.IntegerField(null=True, blank=True)

    # Sekcja: Nazwa wizytowki
    business_name = models.CharField(max_length=500, blank=True)  # nazwa jaka jest w wizytowce

    # Sekcja: Kategorie
    categories = models.JSONField(null=True, blank=True)           # wszystkie kategorie [glowna + poboczne]
    primary_category = models.CharField(max_length=255, blank=True)
    secondary_categories_count = models.IntegerField(null=True, blank=True)

    # Sekcja: Opis
    has_description = models.BooleanField(default=False)
    description_text = models.TextField(blank=True)               # tresc opisu (AI ocenia frazy kluczowe)
    description_length = models.IntegerField(null=True, blank=True)  # znaki (zalecane max 750)

    # Sekcja: Dane kontaktowe
    has_phone = models.BooleanField(default=False)
    has_website = models.BooleanField(default=False)
    website_url = models.CharField(max_length=500, blank=True)    # URL - AI moze ocenic czy to lokalna strona

    # Sekcja: Godziny otwarcia
    has_hours = models.BooleanField(default=False)
    hours_data = models.JSONField(null=True, blank=True)          # godziny dla kazdego dnia tygodnia

    # Sekcja: Zdjecia
    has_main_image = models.BooleanField(default=False)
    photos_count = models.IntegerField(null=True, blank=True)

    # Sekcja: Opinie - zarzadzanie
    owner_responses_ratio = models.FloatField(null=True, blank=True)  # % opinii z odpowiedzia wlasciciela

    # Sekcja: Posty w wizytowce
    POSTS_STATUS_PENDING = 'pending'
    POSTS_STATUS_FETCHED = 'fetched'
    POSTS_STATUS_ERROR = 'error'
    POSTS_STATUS_UNAVAILABLE = 'unavailable'
    POSTS_STATUS_CHOICES = [
        ('pending', 'Pobieranie...'),
        ('fetched', 'Pobrano'),
        ('error', 'Blad'),
        ('unavailable', 'Brak CID'),
    ]
    has_posts = models.BooleanField(default=False)
    posts_count = models.IntegerField(null=True, blank=True)
    posts_count_plus = models.BooleanField(default=False)
    last_post_date = models.DateField(null=True, blank=True)
    posts_status = models.CharField(max_length=20, choices=POSTS_STATUS_CHOICES, default='unavailable')

    # Sekcja: Produkty / Uslugi (Menu)
    has_menu_items = models.BooleanField(default=False)
    menu_items_count = models.IntegerField(null=True, blank=True)

    # Sekcja: Serwisy spolecznosciowe
    has_social_links = models.BooleanField(default=False)
    social_links = models.JSONField(null=True, blank=True)

    # Sekcja: Atrybuty wizytowki
    attributes = models.JSONField(null=True, blank=True)          # np. ogrodek, wifi, rezerwacja, wegetarianskie

    # Wynik analizy
    issues = models.JSONField(null=True, blank=True)

    # Rekomendacje AI
    name_recommendation = models.CharField(max_length=500, blank=True)  # rekomendowana nazwa wizytowki
    description_recommendation = models.TextField(blank=True)           # rekomendowany opis

    # Pola uzupelniane recznie
    has_menu = models.BooleanField(null=True, blank=True)               # None = nie sprawdzono
    has_social_media = models.BooleanField(null=True, blank=True)       # None = nie sprawdzono
    website_recommendations = models.TextField(blank=True)              # zalecenia dot. strony WWW
    custom_summary_items = models.JSONField(default=list, blank=True)   # dodatkowe podpunkty do podsumowania
    show_keyword_searches = models.BooleanField(null=True, blank=True, default=None)  # czy pokazywac wyszukania w PDF
    show_price_list = models.BooleanField(default=False)  # czy dodac cennik do audytu

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


class KeywordSuggestionBatch(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_READY = 'ready'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [
        ('pending', 'Generowanie...'),
        ('ready', 'Gotowe'),
        ('error', 'Blad'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='suggestion_batches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sugestie dla {self.lead.name} ({self.created_at:%d.%m.%Y %H:%M})"


class KeywordSuggestion(models.Model):
    batch = models.ForeignKey(KeywordSuggestionBatch, on_delete=models.CASCADE, related_name='suggestions')
    phrase = models.CharField(max_length=200)
    volume = models.IntegerField(null=True, blank=True)  # miesieczne wyszukiwania
    ai_rank = models.IntegerField(default=0)             # 1-10, im nizej tym lepiej
    ai_reason = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ai_rank']

    def __str__(self):
        return f"{self.phrase} ({self.volume or '?'}/mies.)"


class KeywordRankCheck(models.Model):
    keyword = models.ForeignKey('LeadKeyword', on_delete=models.CASCADE, related_name='rank_checks')
    position = models.IntegerField(null=True, blank=True)  # None = nie znaleziono w top 20
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checked_at']

    def __str__(self):
        pos = self.position or 'brak'
        return f"{self.keyword.phrase}: {pos} ({self.checked_at:%d.%m.%Y})"


class LeadKeyword(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='keywords_list')
    phrase = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.phrase} ({self.lead.name})"


class VoivodeshipKeyword(models.Model):
    """Unikalna fraza kluczowa na poziomie województwa.
    Agreguje frazy ze wszystkich leadów w danym województwie."""
    voivodeship = models.ForeignKey(
        Voivodeship,
        on_delete=models.CASCADE,
        related_name='keywords',
    )
    phrase = models.CharField(max_length=200)
    monthly_searches = models.CharField(
        max_length=50, null=True, blank=True,
        verbose_name='Wyszukania/miesiąc',
    )
    searches_updated_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Data aktualizacji',
    )

    class Meta:
        unique_together = [('voivodeship', 'phrase')]
        ordering = ['phrase']

    def __str__(self):
        return f"{self.phrase} ({self.voivodeship.name})"


class ClientRankSnapshot(models.Model):
    """Zamrozony stan pozycji fraz klienta w danym miesiacu."""
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='rank_snapshots')
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    # JSON: [{"phrase": "fraza", "position": 5}, ...]
    positions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_by = models.CharField(
        max_length=20,
        choices=[('auto', 'Automatyczny'), ('manual', 'Ręczny')],
        default='auto',
    )

    class Meta:
        ordering = ['-year', '-month']
        unique_together = [('lead', 'year', 'month')]

    def __str__(self):
        return f"{self.lead.name} — {self.month:02d}/{self.year}"

    @property
    def label(self):
        import calendar
        return f"{calendar.month_abbr[self.month]} {self.year}"


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


class UserContact(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='contact')
    full_name = models.CharField(max_length=255, blank=True)
    position = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(upload_to='user_photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"


class Pipeline(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    show_on_dashboard = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class PipelineStep(models.Model):
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='steps')
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.pipeline.name} → {self.name}"

    class Meta:
        ordering = ['order']


class LeadPipelineEntry(models.Model):
    lead = models.OneToOneField(Lead, on_delete=models.CASCADE, related_name='pipeline_entry')
    pipeline = models.ForeignKey(Pipeline, on_delete=models.CASCADE, related_name='entries')
    current_step = models.ForeignKey(PipelineStep, on_delete=models.PROTECT, related_name='current_entries')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pipeline_entries')
    entered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.name} → {self.current_step.name}"


class LeadPipelineStepHistory(models.Model):
    entry = models.ForeignKey(LeadPipelineEntry, on_delete=models.CASCADE, related_name='step_history')
    step = models.ForeignKey(PipelineStep, on_delete=models.PROTECT, related_name='history')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='pipeline_step_moves')
    entered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.entry.lead.name} → {self.step.name} ({self.entered_at:%d.%m.%Y})"

    class Meta:
        ordering = ['entered_at']


class ClientActivityLog(models.Model):
    DURATION_CHOICES = [(m, f"{m // 60}h {m % 60:02d}min" if m >= 60 else f"{m} min")
                        for m in range(15, 361, 15)]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        limit_choices_to={'status': 'client'},
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activity_logs')
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    date = models.DateField()
    duration_minutes = models.IntegerField(
        null=True, blank=True,
        verbose_name='Czas trwania',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def duration_label(self):
        if not self.duration_minutes:
            return ''
        h = self.duration_minutes // 60
        m = self.duration_minutes % 60
        if h and m:
            return f"{h}h {m:02d}min"
        elif h:
            return f"{h}h"
        return f"{self.duration_minutes} min"

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.lead.name} — {self.title} ({self.date})"


class AppSettings(models.Model):
    """Singleton — zawsze tylko jeden rekord."""
    openai_api_key = models.CharField(max_length=255, blank=True)
    dataforseo_login = models.CharField(max_length=255, blank=True)
    dataforseo_password = models.CharField(max_length=255, blank=True)
    google_refresh_token = models.TextField(blank=True)  # OAuth2 refresh token do GBP API

    class Meta:
        verbose_name = 'Ustawienia aplikacji'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return 'Ustawienia aplikacji'


class NapDirectoryTag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Nazwa tagu')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag katalogu NAP'
        verbose_name_plural = 'Tagi katalogów NAP'

    def __str__(self):
        return self.name


class NapDirectory(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nazwa katalogu')
    url = models.URLField(max_length=500, verbose_name='Adres WWW')
    is_active = models.BooleanField(default=True, verbose_name='Aktywny')
    notes = models.TextField(blank=True, verbose_name='Notatki')
    tags = models.ManyToManyField(
        NapDirectoryTag,
        blank=True,
        related_name='directories',
        verbose_name='Tagi',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Katalog NAP'
        verbose_name_plural = 'Katalogi NAP'

    def __str__(self):
        return self.name


class LeadNapEntry(models.Model):
    STATUS_ADDED_BY_US = 'added_by_us'
    STATUS_PRE_EXISTING = 'pre_existing'
    STATUS_CHOICES = [
        (STATUS_ADDED_BY_US, 'Dodany przeze mnie'),
        (STATUS_PRE_EXISTING, 'Był przed nami'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='nap_entries',
        verbose_name='Klient',
    )
    directory = models.ForeignKey(
        NapDirectory,
        on_delete=models.CASCADE,
        related_name='lead_entries',
        verbose_name='Katalog NAP',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Status wpisu',
    )
    notes = models.CharField(max_length=500, blank=True, verbose_name='Notatka')
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='nap_entries',
        verbose_name='Oznaczył',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('lead', 'directory')]
        ordering = ['directory__name']
        verbose_name = 'Wpis NAP klienta'
        verbose_name_plural = 'Wpisy NAP klientów'

    def __str__(self):
        return f"{self.lead.name} → {self.directory.name} ({self.get_status_display()})"


class LeadTask(models.Model):
    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Lead',
    )
    title = models.CharField(max_length=500, verbose_name='Zadanie')
    is_done = models.BooleanField(default=False, verbose_name='Wykonane')
    created_at = models.DateTimeField(auto_now_add=True)
    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['is_done', '-created_at']
        verbose_name = 'Zadanie'
        verbose_name_plural = 'Zadania'

    def __str__(self):
        return f"{self.lead.name} — {self.title}"


class TaskBlueprint(models.Model):
    name = models.CharField(max_length=255, verbose_name='Nazwa szablonu')
    description = models.TextField(blank=True, verbose_name='Opis')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Szablon zadań'
        verbose_name_plural = 'Szablony zadań'

    def __str__(self):
        return self.name


class TaskBlueprintItem(models.Model):
    blueprint = models.ForeignKey(
        TaskBlueprint,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Szablon',
    )
    title = models.CharField(max_length=500, verbose_name='Treść zadania')
    order = models.PositiveIntegerField(default=0, verbose_name='Kolejność')

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Pozycja szablonu'
        verbose_name_plural = 'Pozycje szablonu'

    def __str__(self):
        return f"{self.blueprint.name} — {self.title}"


def format_duration(minutes):
    """Formatuje minuty na czytelny string np. 1h 30min, 45 min, 2h."""
    if not minutes:
        return ''
    h = minutes // 60
    m = minutes % 60
    if h and m:
        return f"{h}h {m:02d}min"
    elif h:
        return f"{h}h"
    return f"{minutes} min"


class GBPMetricsSnapshot(models.Model):
    SOURCE_MANUAL = 'manual'
    SOURCE_API = 'api'
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, 'Ręcznie'),
        (SOURCE_API, 'API'),
    ]

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        related_name='gbp_metrics',
        verbose_name='Klient',
    )
    year = models.IntegerField(verbose_name='Rok')
    month = models.IntegerField(verbose_name='Miesiąc')  # 1-12
    day = models.IntegerField(null=True, blank=True, verbose_name='Dzień')  # NULL = wpis miesięczny

    calls = models.IntegerField(null=True, blank=True, verbose_name='Telefony')
    profile_views = models.IntegerField(null=True, blank=True, verbose_name='Wyświetlenia profilu')
    direction_requests = models.IntegerField(null=True, blank=True, verbose_name='Zapytania o trasę')
    website_visits = models.IntegerField(null=True, blank=True, verbose_name='Odwiedziny witryny')

    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default=SOURCE_MANUAL,
        verbose_name='Źródło',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', '-month', '-day']
        verbose_name = 'Metryki GBP'
        verbose_name_plural = 'Metryki GBP'
        unique_together = [('lead', 'year', 'month', 'day', 'source')]

    def __str__(self):
        if self.day:
            return f"{self.lead.name} — {self.day:02d}.{self.month:02d}.{self.year}"
        return f"{self.lead.name} — {self.month:02d}/{self.year}"

    @property
    def label(self):
        import calendar
        if self.day:
            return f"{self.day:02d} {calendar.month_abbr[self.month]} {self.year}"
        return f"{calendar.month_abbr[self.month]} {self.year}"