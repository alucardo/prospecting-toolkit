from django import forms
from .models import City, SearchQuery, Lead, CallLog, CallScript, ImportFile, LeadNote, LeadContact, Pipeline, PipelineStep, LeadPipelineEntry, Voivodeship, ClientActivityLog


class CallLogForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        next_contact_date = cleaned_data.get('next_contact_date')

        if status == 'email_sent' and not next_contact_date:
            self.add_error('next_contact_date', 'Data następnego kontaktu jest wymagana gdy wysłano email.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['script'].queryset = CallScript.objects.filter(is_active=True)
        self.fields['script'].empty_label = '— brak skryptu —'

    class Meta:
        model = CallLog
        fields = ['type', 'status', 'script', 'note', 'next_contact_date']
        widgets = {
            'type': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'note': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Notatka z rozmowy...',
            }),
            'next_contact_date': forms.DateTimeInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'datetime-local',
            }),
            'script': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
        }

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name', 'voivodeship']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Katowice',
            }),
            'voivodeship': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['voivodeship'].queryset = Voivodeship.objects.all()
        self.fields['voivodeship'].empty_label = '— wybierz województwo —'
        self.fields['voivodeship'].required = False

class ImportFileForm(forms.ModelForm):
    class Meta:
        model = ImportFile
        fields = ['city', 'file']
        widgets = {
            'city': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'file': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
            }),
        }

class LeadForm(forms.ModelForm):

    keywords_text = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'np. restauracja Krakow, kuchnia wloska, obiad Swoszowice',
        }),
        label='Frazy kluczowe (oddzielone przecinkami)',
    )

    class Meta:
        model = Lead
        fields = ['city', 'name', 'phone', 'address', 'email', 'website', 'analysis_url', 'google_maps_url', 'source', 'status', 'cold_email_sent', 'email_scraped', 'keyword_search_nationwide']
        widgets = {
            'city': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
            }),
            'address': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
            }),
            'website': forms.URLInput(attrs={
                'class': 'input input-bordered w-full',
            }),
            'analysis_url': forms.URLInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'https://...',
            }),
            'google_maps_url': forms.URLInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'https://maps.app.goo.gl/... lub https://www.google.com/maps/...',
            }),
            'source': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'cold_email_sent': forms.CheckboxInput(attrs={
                'class': 'checkbox',
            }),
            'email_scraped': forms.CheckboxInput(attrs={
                'class': 'checkbox',
            }),
            'keyword_search_nationwide': forms.CheckboxInput(attrs={
                'class': 'checkbox',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.keywords:
            self.fields['keywords_text'].initial = ', '.join(self.instance.keywords)

    def save(self, commit=True):
        instance = super().save(commit=False)
        raw = self.cleaned_data.get('keywords_text', '')
        instance.keywords = [k.strip() for k in raw.split(',') if k.strip()]
        if commit:
            instance.save()
        return instance

class LeadContactForm(forms.ModelForm):
    class Meta:
        model = LeadContact
        fields = ['name', 'phone', 'email', 'note']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Imię i nazwisko',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Numer telefonu',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Adres email',
            }),
            'note': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. szef, kierownik',
            }),
        }


class LeadNoteForm(forms.ModelForm):
    class Meta:
        model = LeadNote
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Treść notatki...',
            }),
        }


class SearchQueryForm(forms.ModelForm):
    source = forms.ChoiceField(
        choices=[(SearchQuery.SOURCE_GOOGLE_MAPS, 'Google Maps')],
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
    )

    class Meta:
        model = SearchQuery
        fields = ['source', 'keyword', 'limit']
        widgets = {
            'keyword': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. restauracje, mechanicy, dentyści',
            }),
            'limit': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
            }),
        }


class PipelineForm(forms.ModelForm):
    class Meta:
        model = Pipeline
        fields = ['name', 'description', 'show_on_dashboard']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Restauracje',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Opcjonalny opis...',
            }),
            'show_on_dashboard': forms.CheckboxInput(attrs={
                'class': 'checkbox',
            }),
        }


class PipelineStepForm(forms.ModelForm):
    class Meta:
        model = PipelineStep
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Pierwszy kontakt',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
            }),
        }


class LeadPipelineEntryForm(forms.ModelForm):
    class Meta:
        model = LeadPipelineEntry
        fields = ['pipeline', 'current_step', 'assigned_to']
        widgets = {
            'pipeline': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'current_step': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'assigned_to': forms.Select(attrs={'class': 'select select-bordered w-full'}),
        }

    def __init__(self, *args, **kwargs):
        pipeline = kwargs.pop('pipeline', None)
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if pipeline:
            self.fields['current_step'].queryset = PipelineStep.objects.filter(pipeline=pipeline)
        else:
            self.fields['current_step'].queryset = PipelineStep.objects.none()
        if user and not self.instance.pk:
            self.fields['assigned_to'].initial = user.pk


class ClientActivityLogForm(forms.ModelForm):
    DURATION_CHOICES = [('', '— brak —')] + [
        (m, f"{m // 60}h {m % 60:02d}min" if m >= 60 else f"{m} min")
        for m in range(15, 361, 15)
    ]

    duration_minutes = forms.ChoiceField(
        choices=DURATION_CHOICES,
        required=False,
        label='Czas trwania',
        widget=forms.Select(attrs={'class': 'select select-bordered w-full'}),
    )

    class Meta:
        model = ClientActivityLog
        fields = ['title', 'description', 'date', 'duration_minutes', 'is_highlighted']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Dodano 15 nowych zdjęć do wizytyówki',
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 4,
                'placeholder': 'Opcjonalny opis szczegółowy...',
            }),
            'date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date',
            }),
            'is_highlighted': forms.CheckboxInput(attrs={
                'class': 'checkbox',
            }),
        }

    def clean_duration_minutes(self):
        val = self.cleaned_data.get('duration_minutes')
        if val == '' or val is None:
            return None
        return int(val)