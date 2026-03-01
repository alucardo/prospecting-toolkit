import requests
import base64
from celery import shared_task
from datetime import datetime
from leads.services.maps_cid_extractor import extract_cid_from_maps_url
from leads.services.dataforseo_posts import fetch_posts, parse_posts

# Alias dla wstecznej kompatybilnosci
extract_keyword_from_maps_url = extract_cid_from_maps_url


def get_dataforseo_business_data(business_name, city, login, password, keyword_override=None):
    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()

    keyword = keyword_override if keyword_override else f"{business_name} {city}"

    payload = [{
        "keyword": keyword,
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
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def extract_business_data(biz):
    """
    Wyciaga wszystkie potrzebne dane z surowej odpowiedzi DataForSEO.
    Mapuje na sekcje audytu wizytowki (zgodnie z raportami BSmarti).
    """
    # --- Podstawowe dane ---
    rating = biz.get('rating', {}).get('value')
    reviews_count = biz.get('rating', {}).get('votes_count', 0) or 0

    # --- Nazwa wizytowki ---
    business_name = biz.get('title', '')

    # --- Kategorie ---
    # DataForSEO zwraca: category (string) + additional_categories (lista stringow)
    primary_category = biz.get('category') or ''
    additional = biz.get('additional_categories') or []
    # Zabezpieczenie na wypadek gdyby additional_categories byl lista slownikow
    if additional and isinstance(additional[0], dict):
        additional = [c.get('name', '') for c in additional if c.get('name')]
    categories = ([primary_category] if primary_category else []) + [c for c in additional if c]
    secondary_categories_count = len(additional)

    # --- Opis ---
    description = biz.get('description') or ''
    has_description = bool(description)
    description_length = len(description) if description else 0

    # --- Dane kontaktowe ---
    phone = biz.get('phone') or ''
    has_phone = bool(phone)
    website_url = biz.get('url') or ''
    has_website = bool(website_url)

    # --- Godziny otwarcia ---
    # DataForSEO: work_time.work_hours.timetable.{day: [{open:{hour,minute}, close:{hour,minute}}]}
    timetable = (biz.get('work_time') or {}).get('work_hours', {}).get('timetable') or {}
    has_hours = bool(timetable)
    DAY_PL = {
        'monday': 'Pon', 'tuesday': 'Wt', 'wednesday': 'Sr',
        'thursday': 'Czw', 'friday': 'Pt', 'saturday': 'Sob', 'sunday': 'Nd',
    }
    DAY_ORDER = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    hours_data = {}
    for day in DAY_ORDER:
        slots = timetable.get(day)
        if slots is None:
            continue
        if not slots:
            hours_data[DAY_PL[day]] = 'zamkniete'
            continue
        slot = slots[0]
        o = slot.get('open', {})
        c = slot.get('close', {})
        oh, om = o.get('hour', 0), o.get('minute', 0)
        ch, cm = c.get('hour', 24), c.get('minute', 0)
        if oh == 0 and om == 0 and ch == 24 and cm == 0:
            hours_data[DAY_PL[day]] = 'całą dobę'
        else:
            hours_data[DAY_PL[day]] = f"{oh:02d}:{om:02d}–{ch:02d}:{cm:02d}"

    # --- Zdjecia ---
    main_image = biz.get('main_image') or ''
    has_main_image = bool(main_image)
    photos_count = biz.get('total_photos') or len(biz.get('photos', []) or [])

    # --- Opinie - odpowiedzi wlasciciela ---
    reviews = biz.get('reviews', []) or []
    if reviews:
        reviews_with_response = sum(1 for r in reviews if r.get('owner_answer'))
        owner_responses_ratio = round(reviews_with_response / len(reviews), 2)
    else:
        owner_responses_ratio = None

    # --- Posty w wizytowce ---
    local_posts = biz.get('local_posts', []) or []
    has_posts = bool(local_posts)
    posts_count = len(local_posts)
    last_post_date = None
    if local_posts:
        dates = []
        for post in local_posts:
            date_str = post.get('date_posted') or post.get('create_time')
            if date_str:
                try:
                    dates.append(datetime.fromisoformat(date_str[:10]).date())
                except Exception:
                    pass
        if dates:
            last_post_date = max(dates)

    # --- Produkty / Uslugi (Menu) ---
    menu = biz.get('menu', []) or biz.get('products', []) or []
    has_menu_items = bool(menu)
    menu_items_count = len(menu) if isinstance(menu, list) else 0

    # --- Serwisy spolecznosciowe ---
    social_links_raw = biz.get('social_links', []) or biz.get('links', []) or []
    # Filtruj tylko social media (FB, IG, itp.)
    social_domains = ['facebook.com', 'instagram.com', 'twitter.com', 'tiktok.com', 'linkedin.com', 'youtube.com']
    social_links = [
        l if isinstance(l, str) else l.get('url', '')
        for l in social_links_raw
        if any(d in str(l) for d in social_domains)
    ]
    has_social_links = bool(social_links)

    # --- Atrybuty wizytowki ---
    attributes = biz.get('attributes', []) or biz.get('feature_list', []) or []

    return {
        'rating': rating,
        'reviews_count': reviews_count,
        'business_name': business_name,
        'categories': categories,
        'primary_category': primary_category,
        'secondary_categories_count': secondary_categories_count,
        'description': description,
        'has_description': has_description,
        'description_length': description_length,
        'phone': phone,
        'has_phone': has_phone,
        'website_url': website_url,
        'has_website': has_website,
        'has_hours': has_hours,
        'hours_data': hours_data,
        'main_image': main_image,
        'has_main_image': has_main_image,
        'photos_count': photos_count,
        'owner_responses_ratio': owner_responses_ratio,
        'has_posts': has_posts,
        'posts_count': posts_count,
        'last_post_date': last_post_date,
        'has_menu_items': has_menu_items,
        'menu_items_count': menu_items_count,
        'has_social_links': has_social_links,
        'social_links': social_links,
        'attributes': attributes,
    }


def detect_issues(data):
    """
    Automatyczna detekcja problemow na podstawie danych wizytowki.
    Odwzorowuje sekcje audytu z raportow BSmarti.
    """
    issues = []
    rating = data.get('rating')
    reviews_count = data.get('reviews_count', 0)

    # Nazwa wizytowki
    business_name = data.get('business_name', '')
    if business_name and '|' not in business_name and len(business_name.split()) < 3:
        issues.append({
            'type': 'warning',
            'section': 'Nazwa wizytowki',
            'text': 'Nazwa nie zawiera slow kluczowych opisujacych typ lokalu (np. "Restauracja Wloska")',
        })

    # Kategorie
    if not data.get('primary_category'):
        issues.append({'type': 'error', 'section': 'Kategoria glowna', 'text': 'Brak kategorii glownej'})
    sec_count = data.get('secondary_categories_count', 0) or 0
    if sec_count == 0:
        issues.append({'type': 'warning', 'section': 'Kategorie poboczne', 'text': 'Brak kategorii pobocznych — dodaj 2-4 strategiczne kategorie'})
    elif sec_count < 2:
        issues.append({'type': 'warning', 'section': 'Kategorie poboczne', 'text': f'Tylko {sec_count} kategoria poboczna — zalecane minimum 2-4'})

    # Opis
    if not data.get('has_description'):
        issues.append({'type': 'error', 'section': 'Opis', 'text': 'Brak opisu wizytowki — kluczowe dla SEO i decyzji klientow'})
    elif data.get('description_length', 0) < 200:
        issues.append({'type': 'warning', 'section': 'Opis', 'text': f'Opis jest bardzo krotki ({data["description_length"]} znakow) — zalecane 400-750 znakow'})
    elif data.get('description_length', 0) > 750:
        issues.append({'type': 'warning', 'section': 'Opis', 'text': f'Opis przekracza 750 znakow ({data["description_length"]}) — Google moze go obciac'})

    # Dane kontaktowe
    if not data.get('has_website'):
        issues.append({'type': 'error', 'section': 'Strona internetowa', 'text': 'Brak strony internetowej w wizytowce'})
    if not data.get('has_phone'):
        issues.append({'type': 'warning', 'section': 'Numer telefonu', 'text': 'Brak numeru telefonu'})

    # Godziny otwarcia
    if not data.get('hours_data'):
        issues.append({'type': 'error', 'section': 'Godziny otwarcia', 'text': 'Brak godzin otwarcia — klienci nie wiedza kiedy przyjsc'})

    # Zdjecia
    if not data.get('has_main_image'):
        issues.append({'type': 'warning', 'section': 'Zdjecia', 'text': 'Brak zdjecia glownego (okladkowego)'})
    photos_count = data.get('photos_count', 0) or 0
    if photos_count == 0:
        issues.append({'type': 'error', 'section': 'Zdjecia', 'text': 'Brak zdiec w wizytowce'})
    elif photos_count < 10:
        issues.append({'type': 'warning', 'section': 'Zdjecia', 'text': f'Malo zdiec ({photos_count}) — zalecane minimum 10-20, szczegolnie potraw z ludzmi'})

    # Opinie
    if rating is not None and rating < 4.0:
        issues.append({'type': 'error', 'section': 'Opinie', 'text': f'Niska ocena ({rating}) — wymaga aktywnego zarzadzania opiniami'})
    elif rating is not None and rating < 4.5:
        issues.append({'type': 'warning', 'section': 'Opinie', 'text': f'Ocena {rating} — jest potencjal do poprawy (cel: 4.5+)'})
    if reviews_count < 20:
        issues.append({'type': 'warning', 'section': 'Opinie', 'text': f'Malo opinii ({reviews_count}) — zalecane minimum 20-50'})

    # Odpowiedzi wlasciciela na opinie
    ratio = data.get('owner_responses_ratio')
    if ratio is None or ratio == 0:
        issues.append({'type': 'warning', 'section': 'Opinie', 'text': 'Wlasciciel nie odpowiada na opinie — to wazny sygnal dla Google i klientow'})
    elif ratio < 0.5:
        issues.append({'type': 'warning', 'section': 'Opinie', 'text': f'Wlasciciel odpowiada tylko na {int(ratio*100)}% opinii — zalecane odpowiadac na wszystkie'})

    # Posty - sprawdzamy tylko jesli mamy pewnosc (CID byl dostepny)
    if data.get('posts_verified'):
        if not data.get('has_posts'):
            issues.append({'type': 'warning', 'section': 'Posty', 'text': 'Brak postow w wizytowce — posty sygnalizuja aktywnosc i wspieraja widocznosc'})
        else:
            last_post = data.get('last_post_date')
            if last_post:
                from datetime import date
                days_ago = (date.today() - last_post).days
                if days_ago > 60:
                    issues.append({'type': 'warning', 'section': 'Posty', 'text': f'Ostatni post byl {days_ago} dni temu — zalecane dodawac co 1-2 tygodnie'})

    # Atrybuty
    if not data.get('attributes'):
        issues.append({'type': 'warning', 'section': 'Atrybuty', 'text': 'Brak atrybutow wizytowki (np. ogrodek, mozliwosc rezerwacji, dania wegetarianskie)'})

    return issues


def analyze_with_openai(lead_name, city, data, api_key, keywords=None):
    issues = detect_issues(data)

    # Zbuduj opis godzin
    hours_desc = 'brak'
    if data.get('hours_data'):
        hours_lines = []
        for day, times in data['hours_data'].items():
            if isinstance(times, dict):
                hours_lines.append(f"{day}: {times.get('open', '?')} - {times.get('close', '?')}")
            else:
                hours_lines.append(f"{day}: {times}")
        hours_desc = ', '.join(hours_lines[:3]) + ('...' if len(hours_lines) > 3 else '')

    # Opis do AI - surowa tresc jesli krotka, skrocona jesli dluga
    desc_for_ai = data.get('description', '') or 'BRAK'
    if len(desc_for_ai) > 400:
        desc_for_ai = desc_for_ai[:400] + '...'

    # Lista problemow dla AI
    issues_text = '\n'.join([f"- [{i['section']}] {i['text']}" for i in issues]) if issues else 'Brak wykrytych problemow'

    keywords_str = ', '.join(keywords) if keywords else 'nie podano'

    prompt = f"""Jestes ekspertem od optymalizacji wizytowek Google Business Profile dla lokali gastronomicznych. Pracujesz dla agencji marketingowej BSmarti i przygotowujesz krotkie podsumowanie audytu ktore zostanie pokazane handlowcowi przed rozmowa z wlascicielem lokalu.

Analizujesz wizytowke: {lead_name} ({city})

=== FRAZY KLUCZOWE NA KTORE MA BYC WIDOCZNA WIZYTOWKA ===
{keywords_str}

Kazda sekcja ponizej powinna byc oceniana pod katem tych fraz:
- NAZWA: czy zawiera slowa opisujace typ lokalu i lokalizacje z tych fraz?
- OPIS: czy frazy sa uzyte naturalnie w tresci opisu?
- KATEGORIE: czy pokrywaja sie z tematami fraz?
- POSTY: czy tematyka postow jest zgodna z frazami?
- GODZINY: czy lokal jest otwarty w godzinach gdy klienci szukaja (np. lunch, kolacja)?

=== DANE Z WIZYTOWKI ===
Nazwa w wizytowce: {data.get('business_name') or lead_name}
Kategoria glowna: {data.get('primary_category') or 'BRAK'}
Kategorie poboczne: {data.get('secondary_categories_count', 0)} szt.
Opis: {desc_for_ai}
Dlugosc opisu: {data.get('description_length', 0)} znakow (zalecane 400-750)
Strona WWW: {data.get('website_url') or 'BRAK'}
Telefon: {'tak' if data.get('has_phone') else 'BRAK'}
Godziny otwarcia: {hours_desc}
Zdjecia: {data.get('photos_count', 0)} szt.{' (brak zdjecia glownego)' if not data.get('has_main_image') else ''}
Ocena: {data.get('rating') or 'brak'} / 5.0
Liczba opinii: {data.get('reviews_count', 0)}
Odpowiedzi wlasciciela na opinie: {f"{int(data['owner_responses_ratio']*100)}%" if data.get('owner_responses_ratio') is not None else 'brak danych'}
Posty w wizytowce: {'tak, ostatni: ' + str(data.get('last_post_date')) if data.get('has_posts') else 'BRAK'}
Atrybuty (ogrodek, wifi itp.): {'uzupelnione' if data.get('attributes') else 'BRAK'}

=== WYKRYTE PROBLEMY ===
{issues_text}

=== ZADANIE ===
Napisz krotka analize (max 250 slow) w jezyku polskim w 3 czesciach:

1. OCENA OGOLNA (1-2 zdania): Ogolny stan wizytowki i jak dobrze jest dopasowana do podanych fraz kluczowych.

2. TOP 3 PROBLEMY DO NAPRAWIENIA: Wymien 3 najwazniejsze rzeczy ktore wlasciciel powinien zmienic. Tam gdzie to mozliwe, odnosnik do konkretnej frazy kluczowej (np. "nazwa nie zawiera slowa restauracja z frazy X").

3. PROPOZYCJA WSPOLPRACY (2-3 zdania): Napisz jak handlowiec moze zaproponowac pomoc. Badz konkretny — co agencja zrobi i jaki efekt to przyniesie (wiecej klientow, wyzsze pozycje w Google Maps dla fraz: {keywords_str}).

Pisz profesjonalnie ale przystepnie. Unikaj slow takich jak "kluczowy" lub "istotny". Badz konkretny i rzeczowy."""

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


def _save_business_data(lead, biz, status):
    """Pomocnicza: zapisuje sparsowane dane wizytowki do bazy."""
    data = extract_business_data(biz)
    issues = detect_issues(data)
    return GoogleBusinessAnalysis.objects.create(
        lead=lead,
        raw_data=biz,
        status=status,
        keywords_used=[],
        issues=issues,
        ai_summary='',
        rating=data['rating'],
        reviews_count=data['reviews_count'],
        business_name=data['business_name'],
        categories=data['categories'],
        primary_category=data['primary_category'],
        secondary_categories_count=data['secondary_categories_count'],
        has_description=data['has_description'],
        description_text=data['description'],
        description_length=data['description_length'],
        has_phone=data['has_phone'],
        has_website=data['has_website'],
        website_url=data['website_url'],
        has_hours=data['has_hours'],
        hours_data=data['hours_data'],
        has_main_image=data['has_main_image'],
        photos_count=data['photos_count'],
        owner_responses_ratio=data['owner_responses_ratio'],
        has_posts=data['has_posts'],
        posts_count=data['posts_count'],
        last_post_date=data['last_post_date'],
        has_menu_items=data['has_menu_items'],
        menu_items_count=data['menu_items_count'],
        has_social_links=data['has_social_links'],
        social_links=data['social_links'],
        attributes=data['attributes'],
    )


@shared_task
def generate_keyword_suggestions(lead_id, batch_id):
    """Generuje sugestie fraz: DataForSEO → scrape WWW → GPT top 10."""
    from .models import Lead, KeywordSuggestionBatch, KeywordSuggestion, AppSettings
    import json

    lead = Lead.objects.get(pk=lead_id)
    batch = KeywordSuggestionBatch.objects.get(pk=batch_id)
    app_settings = AppSettings.get()

    try:
        # 1. Pobierz sugestie fraz z DataForSEO
        seed_phrase = f"{lead.name} {lead.city.name}"
        credentials = base64.b64encode(
            f"{app_settings.dataforseo_login}:{app_settings.dataforseo_password}".encode()
        ).decode()

        dfs_response = requests.post(
            "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live",
            headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
            json=[{"keyword": seed_phrase, "language_name": "Polish", "location_name": "Poland", "limit": 50}],
            timeout=60,
        )
        dfs_response.raise_for_status()
        dfs_data = dfs_response.json()
        raw_keywords = []
        items = dfs_data.get('tasks', [{}])[0].get('result', [{}])[0].get('items', [])
        for item in items:
            kw = item.get('keyword', '')
            vol = (item.get('keyword_info') or {}).get('search_volume') or 0
            if kw:
                raw_keywords.append({'phrase': kw, 'volume': vol})

        # 2. Scrape strony WWW jesli istnieje (pomijamy social media)
        from .constants import is_blocked_for_scraping
        website_text = ''
        if lead.website and not is_blocked_for_scraping(lead.website):
            try:
                resp = requests.get(lead.website, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                resp.raise_for_status()
                # Wyciagnij czysty tekst
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', resp.text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                website_text = text[:3000]  # max 3000 znakow dla AI
            except Exception:
                website_text = ''

        # 3. GPT wybiera top 10
        keywords_for_ai = json.dumps(
            [{'fraza': k['phrase'], 'wyszukiwania': k['volume']} for k in raw_keywords[:50]],
            ensure_ascii=False
        )
        website_section = f"\n\nTRESC STRONY WWW ({lead.website}):\n{website_text}" if website_text else ''

        # Frazy juz dodane - AI ma je pominac
        existing_phrases = list(lead.keywords_list.values_list('phrase', flat=True))
        existing_section = f"\n\nFRAZY JUZ DODANE (nie proponuj ich ponownie):\n" + '\n'.join(f'- {p}' for p in existing_phrases) if existing_phrases else ''

        prompt = f"""Jestes ekspertem SEO lokalnego. Twoje zadanie to wybrac 10 najlepszych fraz kluczowych dla wizytowki Google Maps lokalu.

LOKAL: {lead.name}
MIASTO: {lead.city.name}
KATEGORIA: {lead.business_analyses.filter(status='analyzed').values_list('primary_category', flat=True).first() or 'nieznana'}
OPIS WIZYTOWKI: {lead.business_analyses.filter(status='analyzed').values_list('description_text', flat=True).first() or 'brak'}{website_section}{existing_section}

DOSTEPNE FRAZY Z DANYMI WYSZUKIWAN:
{keywords_for_ai}

Wybierz dokladnie 10 fraz ktore:
1. Sa najlepiej dopasowane do tego konkretnego biznesu
2. Maja realne szanse na pojawienie sie w wynikach Google Maps
3. Lacza intencje zakupowa z lokalizacja

Odpowiedz TYLKO jako JSON, bez zadnego tekstu przed ani po:
[
  {{"fraza": "...", "wyszukiwania": 0, "uzasadnienie": "max 80 znakow"}},
  ...
]"""

        ai_response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {app_settings.openai_api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 1024},
            timeout=60,
        )
        ai_response.raise_for_status()
        ai_text = ai_response.json()['choices'][0]['message']['content'].strip()

        # Wyczysc markdown jesli AI dodal ```json
        ai_text = re.sub(r'^```json\s*', '', ai_text, flags=re.MULTILINE)
        ai_text = re.sub(r'^```\s*', '', ai_text, flags=re.MULTILINE)
        suggestions = json.loads(ai_text)

        # Zapisz sugestie
        for rank, s in enumerate(suggestions[:10], start=1):
            # Znajdz volume z DataForSEO (AI moze go zmienic)
            matched_volume = next((k['volume'] for k in raw_keywords if k['phrase'] == s.get('fraza')), s.get('wyszukiwania'))
            KeywordSuggestion.objects.create(
                batch=batch,
                phrase=s.get('fraza', ''),
                volume=matched_volume,
                ai_rank=rank,
                ai_reason=s.get('uzasadnienie', '')[:300],
            )

        batch.status = 'ready'
        batch.save()

    except Exception as e:
        batch.status = 'error'
        batch.error_message = str(e)
        batch.save()


@shared_task
def check_keyword_rankings(lead_id, keyword_ids=None):
    """Sprawdza pozycje wizytowki. Jesli keyword_ids podane - tylko te frazy, inaczej wszystkie."""
    from .models import Lead, LeadKeyword, KeywordRankCheck, AppSettings

    lead = Lead.objects.get(pk=lead_id)
    app_settings = AppSettings.get()
    keywords = lead.keywords_list.filter(pk__in=keyword_ids) if keyword_ids else lead.keywords_list.all()

    if not keywords:
        return
    if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
        return

    # Pobierz CID wizytowki zeby dopasowac wynik
    cid_str = extract_keyword_from_maps_url(lead.google_maps_url)
    cid_number = None
    if cid_str and cid_str.startswith('cid:'):
        try:
            cid_number = int(cid_str[4:])
        except ValueError:
            pass

    credentials = base64.b64encode(
        f"{app_settings.dataforseo_login}:{app_settings.dataforseo_password}".encode()
    ).decode()

    for kw in keywords:
        try:
            # Uzyj SERP Maps endpoint - zwraca ranked liste biznesow
            payload = {
                "keyword": kw.phrase,
                "language_name": "Polish",
                "depth": 20,
            }
            if lead.city.location_coordinate:
                payload["location_coordinate"] = lead.city.location_coordinate
            else:
                payload["location_name"] = "Poland"

            response = requests.post(
                "https://api.dataforseo.com/v3/serp/google/maps/live/advanced",
                headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
                json=[payload],
                timeout=60,
            )
            response.raise_for_status()
            items = response.json().get('tasks', [{}])[0].get('result', [{}])[0].get('items', [])

            position = None
            for item in items:
                item_cid = item.get('cid')
                # Porownuj CID jako string i int
                cid_match = cid_number and (
                    item_cid == cid_number or
                    str(item_cid) == str(cid_number)
                )
                # Dopasowanie po nazwie jako fallback
                name_match = not cid_number and lead.name.lower() in (item.get('title') or '').lower()

                if cid_match or name_match:
                    position = item.get('rank_absolute')
                    break

            KeywordRankCheck.objects.create(keyword=kw, position=position)

        except Exception as e:
            KeywordRankCheck.objects.create(keyword=kw, position=None)


@shared_task
def fetch_google_business_data(lead_id, analysis_id=None):
    """Krok 1: Pobiera dane z DataForSEO i zapisuje. Bez AI."""
    from .models import Lead, GoogleBusinessAnalysis, AppSettings

    lead = Lead.objects.get(pk=lead_id)
    app_settings = AppSettings.get()

    def fail(text, raw=None):
        """Pomocnicza: oznacza rekord jako blad."""
        if analysis_id:
            GoogleBusinessAnalysis.objects.filter(pk=analysis_id).update(
                status='error',
                raw_data=raw or {},
                issues=[{'type': 'error', 'section': 'System', 'text': text}],
            )
        else:
            GoogleBusinessAnalysis.objects.create(
                lead=lead, status='error', ai_summary='',
                issues=[{'type': 'error', 'section': 'System', 'text': text}],
            )

    if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
        fail('Brak konfiguracji DataForSEO w ustawieniach')
        return

    try:
        keyword_override = extract_keyword_from_maps_url(lead.google_maps_url)
        result = get_dataforseo_business_data(
            lead.name, lead.city.name,
            app_settings.dataforseo_login,
            app_settings.dataforseo_password,
            keyword_override=keyword_override,
        )
        # Pobierz frazy z nowego modelu LeadKeyword
        keywords_from_model = list(lead.keywords_list.values_list('phrase', flat=True))

        items = result.get('tasks', [{}])[0].get('result', [{}])[0].get('items', [])

        if not items:
            fail('Nie znaleziono wizytowki w Google', raw=result)
            return

        biz = items[0]
        data = extract_business_data(biz)

        # Posty pobieramy w tle osobnym taskiem
        data['posts_verified'] = False
        posts_status = 'pending'

        issues = detect_issues(data)

        fields = dict(
            raw_data=biz,
            status='fetched',
            keywords_used=[],
            issues=issues,
            ai_summary='',
            rating=data['rating'],
            reviews_count=data['reviews_count'],
            business_name=data['business_name'],
            categories=data['categories'],
            primary_category=data['primary_category'],
            secondary_categories_count=data['secondary_categories_count'],
            has_description=data['has_description'],
            description_text=data['description'],
            description_length=data['description_length'],
            has_phone=data['has_phone'],
            has_website=data['has_website'],
            website_url=data['website_url'],
            has_hours=data['has_hours'],
            hours_data=data['hours_data'],
            has_main_image=data['has_main_image'],
            photos_count=data['photos_count'],
            owner_responses_ratio=data['owner_responses_ratio'],
            has_posts=data['has_posts'],
            posts_count=data['posts_count'],
            posts_count_plus=data.get('posts_count_plus', False),
            last_post_date=data['last_post_date'],
            posts_status=posts_status,
            has_menu_items=data['has_menu_items'],
            menu_items_count=data['menu_items_count'],
            has_social_links=data['has_social_links'],
            social_links=data['social_links'],
            attributes=data['attributes'],
        )

        if analysis_id:
            GoogleBusinessAnalysis.objects.filter(pk=analysis_id).update(**fields)
            saved_id = analysis_id
        else:
            obj = GoogleBusinessAnalysis.objects.create(lead=lead, **fields)
            saved_id = obj.pk

        # Odpal background task do pobrania postow (uzywamy nazwy firmy jako keyword)
        fetch_business_posts.delay(saved_id, lead.name)

    except Exception as e:
        fail(str(e))


@shared_task
def run_google_business_analysis(analysis_id, keywords=None):
    """Krok 2: Uruchamia AI na juz pobranych danych. Aktualizuje rekord."""
    from .models import GoogleBusinessAnalysis, AppSettings

    analysis = GoogleBusinessAnalysis.objects.get(pk=analysis_id)
    app_settings = AppSettings.get()

    if not app_settings.openai_api_key:
        analysis.status = 'error'
        analysis.ai_summary = 'Blad: Brak klucza OpenAI API w ustawieniach'
        analysis.save()
        return

    try:
        data = extract_business_data(analysis.raw_data)
        # Nie nadpisuj posts_verified — posty pobiera osobny task
        data['posts_verified'] = False
        issues, ai_summary = analyze_with_openai(
            analysis.lead.name, analysis.lead.city.name,
            data, app_settings.openai_api_key,
            keywords=keywords or [],
        )
        analysis.issues = issues
        analysis.ai_summary = ai_summary
        analysis.keywords_used = keywords or []
        analysis.status = 'analyzed'
        analysis.save()
    except Exception as e:
        analysis.status = 'error'
        analysis.ai_summary = f'Blad AI: {str(e)}'
        analysis.save()


@shared_task
def fetch_business_posts(analysis_id, keyword):
    """Background task: pobiera posty wizytowki i aktualizuje analize."""
    from .models import GoogleBusinessAnalysis, AppSettings
    from leads.services.dataforseo_posts import fetch_posts, parse_posts

    app_settings = AppSettings.get()
    if not app_settings.dataforseo_login or not app_settings.dataforseo_password:
        GoogleBusinessAnalysis.objects.filter(pk=analysis_id).update(posts_status='error')
        return

    raw_posts = fetch_posts(keyword, app_settings.dataforseo_login, app_settings.dataforseo_password)

    if raw_posts is None:  # timeout lub blad
        GoogleBusinessAnalysis.objects.filter(pk=analysis_id).update(posts_status='error')
        return

    posts_data = parse_posts(raw_posts)
    GoogleBusinessAnalysis.objects.filter(pk=analysis_id).update(
        posts_status='fetched',
        has_posts=posts_data['has_posts'],
        posts_count=posts_data['posts_count'],
        posts_count_plus=posts_data['posts_count_plus'],
        last_post_date=posts_data['last_post_date'],
    )
