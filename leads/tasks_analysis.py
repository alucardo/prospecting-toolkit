import requests
import base64
from celery import shared_task


def get_dataforseo_business_data(business_name, city, login, password):
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    payload = [{
        "keyword": f"{business_name} {city}",
        "location_name": "Poland",
        "language_name": "Polish",
    }]

    response = requests.post(
        "https://api.dataforseo.com/v3/business_data/google/my_business_info/live",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def analyze_with_openai(business_name, city, data, api_key):
    issues = []

    rating = data.get('rating')
    reviews_count = data.get('reviews_count', 0)
    description = data.get('description')
    website = data.get('website')
    phone = data.get('phone')
    work_hours = data.get('work_hours')
    main_image = data.get('main_image')
    photos_count = data.get('photos_count', 0)
    categories = data.get('categories', [])

    if not description:
        issues.append({'type': 'error', 'text': 'Brak opisu wizytówki'})
    if not website:
        issues.append({'type': 'error', 'text': 'Brak strony internetowej'})
    if not phone:
        issues.append({'type': 'warning', 'text': 'Brak numeru telefonu'})
    if not work_hours:
        issues.append({'type': 'warning', 'text': 'Brak godzin otwarcia'})
    if not main_image:
        issues.append({'type': 'warning', 'text': 'Brak zdjęcia głównego'})
    if photos_count < 10:
        issues.append({'type': 'warning', 'text': f'Mało zdjęć ({photos_count}) — zalecane minimum 10'})
    if rating and rating < 4.0:
        issues.append({'type': 'error', 'text': f'Niska ocena ({rating}) — wymaga działań'})
    if reviews_count < 20:
        issues.append({'type': 'warning', 'text': f'Mało opinii ({reviews_count}) — zalecane minimum 20'})
    if not categories:
        issues.append({'type': 'warning', 'text': 'Brak kategorii'})

    prompt = f"""Jesteś ekspertem od optymalizacji wizytówek Google Business Profile dla lokali gastronomicznych.

Analizujesz wizytówkę: {business_name} ({city})

Dane z wizytówki:
- Ocena: {rating or 'brak'}
- Liczba opinii: {reviews_count}
- Opis: {'tak' if description else 'BRAK'}
- Strona WWW: {website or 'BRAK'}
- Telefon: {'tak' if phone else 'BRAK'}
- Godziny otwarcia: {'tak' if work_hours else 'BRAK'}
- Liczba zdjęć: {photos_count}
- Kategorie: {', '.join(categories) if categories else 'BRAK'}

Przygotuj krótką analizę (max 300 słów) w języku polskim:
1. Oceń ogólny stan wizytówki (1-2 zdania)
2. Wymień 3 najważniejsze problemy do naprawienia
3. Podaj 2-3 konkretne działania które możesz zaproponować właścicielowi jako usługę

Pisz jak doświadczony handlowiec który chce przekonać właściciela do współpracy. Bądź konkretny i rzeczowy."""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        },
        timeout=60,
    )
    response.raise_for_status()
    ai_summary = response.json()['choices'][0]['message']['content']

    return issues, ai_summary


@shared_task
def analyze_google_business(lead_id):
    from .models import Lead, GoogleBusinessAnalysis, AppSettings

    lead = Lead.objects.get(pk=lead_id)
    app_settings = AppSettings.get()

    if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
        GoogleBusinessAnalysis.objects.create(
            lead=lead,
            ai_summary='Błąd: Brak konfiguracji DataForSEO w ustawieniach aplikacji.',
            issues=[{'type': 'error', 'text': 'Brak konfiguracji DataForSEO'}],
        )
        return

    if not app_settings.openai_api_key:
        GoogleBusinessAnalysis.objects.create(
            lead=lead,
            ai_summary='Błąd: Brak klucza OpenAI API w ustawieniach aplikacji.',
            issues=[{'type': 'error', 'text': 'Brak klucza OpenAI API'}],
        )
        return

    try:
        result = get_dataforseo_business_data(
            lead.name, lead.city.name,
            app_settings.dataforseo_login,
            app_settings.dataforseo_password,
        )

        items = (
            result
            .get('tasks', [{}])[0]
            .get('result', [{}])[0]
            .get('items', [])
        )

        if not items:
            GoogleBusinessAnalysis.objects.create(
                lead=lead,
                raw_data=result,
                ai_summary='Nie znaleziono wizytówki Google dla tej firmy.',
                issues=[{'type': 'error', 'text': 'Nie znaleziono wizytówki w Google'}],
            )
            return

        biz = items[0]

        rating = biz.get('rating', {}).get('value')
        reviews_count = biz.get('rating', {}).get('votes_count', 0)
        description = biz.get('description')
        website = biz.get('url')
        phone = biz.get('phone')
        work_hours = biz.get('work_hours')
        main_image = biz.get('main_image')
        photos_count = len(biz.get('photos', []))
        categories = [c.get('name', '') for c in biz.get('categories', [])]

        flat_data = {
            'rating': rating,
            'reviews_count': reviews_count,
            'description': description,
            'website': website,
            'phone': phone,
            'work_hours': work_hours,
            'main_image': main_image,
            'photos_count': photos_count,
            'categories': categories,
        }

        issues, ai_summary = analyze_with_openai(
            lead.name, lead.city.name,
            flat_data,
            app_settings.openai_api_key,
        )

        GoogleBusinessAnalysis.objects.create(
            lead=lead,
            raw_data=biz,
            rating=rating,
            reviews_count=reviews_count,
            has_description=bool(description),
            has_website=bool(website),
            has_phone=bool(phone),
            has_hours=bool(work_hours),
            photos_count=photos_count,
            categories=categories,
            ai_summary=ai_summary,
            issues=issues,
        )

    except Exception as e:
        GoogleBusinessAnalysis.objects.create(
            lead=lead,
            raw_data={'error': str(e)},
            ai_summary=f'Błąd podczas analizy: {str(e)}',
            issues=[{'type': 'error', 'text': f'Błąd: {str(e)}'}],
        )
