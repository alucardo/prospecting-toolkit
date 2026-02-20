from django import forms
from .models import City, SearchQuery


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