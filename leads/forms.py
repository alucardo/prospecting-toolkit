from django import forms
from .models import City, SearchQuery, Lead, CallLog, ImportFile


class CallLogForm(forms.ModelForm):
    class Meta:
        model = CallLog
        fields = ['status', 'note', 'next_contact_date']
        widgets = {
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
    class Meta:
        model = Lead
        fields = ['city', 'name', 'phone', 'address', 'email', 'website', 'source', 'status']
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
            'source': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'status': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
        }

class SearchQueryForm(forms.ModelForm):
    class Meta:
        model = SearchQuery
        fields = ['keyword', 'limit']
        widgets = {
            'keyword': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'np. restauracje, mechanicy, dentyści',
            }),
            'limit': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
            }),
        }