import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('prospecting_toolkit')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Sprawdzanie pozycji fraz — poniedziałek i czwartek o 1:00 w nocy
    'check-rankings-monday': {
        'task': 'leads.tasks_analysis.check_all_clients_rankings',
        'schedule': crontab(hour=1, minute=0, day_of_week='monday'),
    },
    'check-rankings-thursday': {
        'task': 'leads.tasks_analysis.check_all_clients_rankings',
        'schedule': crontab(hour=1, minute=0, day_of_week='thursday'),
    },
    # Snapshot miesięczny — 1. dnia każdego miesiąca o 2:00 w nocy
    'monthly-snapshot': {
        'task': 'leads.tasks_analysis.monthly_snapshot_all_clients',
        'schedule': crontab(hour=2, minute=0, day_of_month='1'),
    },
}

app.conf.timezone = 'Europe/Warsaw'
