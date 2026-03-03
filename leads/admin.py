from django.contrib import admin

# Register your models here.
from .models import City, SearchQuery, Lead, CallLog, KeywordSuggestionBatch


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'city', 'status', 'created_at']
    list_filter = ['status', 'city']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'city', 'source', 'created_at']
    list_filter = ['source', 'city']
    search_fields = ['name', 'phone', 'email']

@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ['lead', 'status', 'next_contact_date', 'called_at']
    list_filter = ['status']

@admin.register(KeywordSuggestionBatch)
class KeywordSuggestionBatchAdmin(admin.ModelAdmin):
    list_display = ['lead', 'status', 'created_at']
    readonly_fields = ['error_message']