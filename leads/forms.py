from django import forms
from .models import City, SearchQuery, Lead, CallLog, ImportFile, LeadNote, LeadContact


class CallLogForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        next_contact_date = cleaned_data.get('next_contact_date')

        if status == 'email_sent' and not next_contact_date:
            self.add_error('next_contact_date', 'Data następnego kontaktu jest wymagana gdy wysłano email.')

        return cleaned_data

    class Meta:
        model = CallLog
        fields = ['type', 'status', 'note', 'next_contact_date']
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
            'next_contact_date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date',
            }),
        }

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. Katowice',
            })
        }

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
        fields = ['city', 'name', 'phone', 'address', 'email', 'website', 'analysis_url', 'google_maps_url', 'source', 'status', 'cold_email_sent', 'email_scraped']
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