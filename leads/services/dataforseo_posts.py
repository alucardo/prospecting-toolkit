import requests
import base64
import time
from datetime import datetime


def fetch_posts(keyword, login, password):
    """
    Pobiera posty z wizytowki Google przez DataForSEO.
    Uzywa metody asynchronicznej: task_post -> polling task_get.
    'keyword' to nazwa firmy (nie CID) - np. "Hana Sushi".
    Zwraca liste postow, [] jesli brak, None jesli blad.
    """
    if not keyword or not login or not password:
        return None

    credentials = base64.b64encode(f"{login}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }

    # Krok 1: Utworz zadanie
    try:
        r = requests.post(
            "https://api.dataforseo.com/v3/business_data/google/my_business_updates/task_post",
            headers=headers,
            json=[{
                "keyword": keyword,
                "location_name": "Poland",
                "language_name": "Polish",
                "depth": 10,
            }],
            timeout=30,
        )
        r.raise_for_status()
        task = r.json().get('tasks', [{}])[0]
        task_id = task.get('id')
        if not task_id:
            return None
    except Exception:
        return None

    # Krok 2: Polling az do wyniku (max ~90s)
    for attempt in range(9):
        time.sleep(10)
        try:
            r2 = requests.get(
                f"https://api.dataforseo.com/v3/business_data/google/my_business_updates/task_get/{task_id}",
                headers=headers,
                timeout=30,
            )
            r2.raise_for_status()
            task_result = r2.json().get('tasks', [{}])[0]
            status_code = task_result.get('status_code')

            if status_code == 20000:
                items = (task_result.get('result') or [{}])[0].get('items') or []
                return items
            elif status_code in (40602, 40601):
                # Task In Queue / Task In Progress - czekaj dalej
                continue
            else:
                # Inny blad
                return None
        except Exception:
            continue

    return None  # timeout po 90s


def parse_posts(posts):
    """
    Parsuje liste postow z DataForSEO.
    Zwraca slownik z has_posts, posts_count, posts_count_plus, last_post_date.
    """
    if not posts:
        return {
            'has_posts': False,
            'posts_count': 0,
            'posts_count_plus': False,
            'last_post_date': None,
        }

    dates = []
    for post in posts:
        # my_business_updates zwraca 'timestamp', nie 'date_posted'
        date_str = post.get('timestamp') or post.get('date_posted') or post.get('create_time')
        if date_str:
            try:
                dates.append(datetime.fromisoformat(date_str[:10]).date())
            except Exception:
                pass

    last_post_date = max(dates) if dates else None
    posts_count = len(posts)
    posts_count_plus = posts_count >= 10

    return {
        'has_posts': True,
        'posts_count': posts_count,
        'posts_count_plus': posts_count_plus,
        'last_post_date': last_post_date,
    }
