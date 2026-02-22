import re
import requests
from bs4 import BeautifulSoup

from leads.constants import is_blocked_for_scraping

EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

CONTACT_PAGE_SLUGS = [
    '/kontakt', '/contact', '/kontaktiere-uns',
    '/o-nas', '/about', '/about-us',
]

LEGAL_PAGE_SLUGS = [
    '/regulamin', '/polityka-prywatnosci', '/privacy-policy',
    '/terms', '/rodo',
]


def is_facebook(url):
    return is_blocked_for_scraping(url)


def find_emails_in_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    emails = []
    for tag in soup.find_all('a', href=True):
        if tag['href'].startswith('mailto:'):
            email = tag['href'].replace('mailto:', '').split('?')[0].strip()
            if email:
                emails.append(email)

    text_emails = re.findall(EMAIL_REGEX, soup.get_text())
    emails.extend(text_emails)

    emails = [e for e in emails if '.' in e.split('@')[1]]

    return list(set(emails))


def fetch_page(url, timeout=10):
    try:
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; EmailScraper/1.0)'
        })
        if response.status_code == 200:
            return response.text
    except Exception:
        pass
    return None


def find_contact_page_url(base_url, html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all('a', href=True):
        href = tag['href'].lower()
        for slug in CONTACT_PAGE_SLUGS:
            if slug in href:
                if href.startswith('http'):
                    return tag['href']
                return base_url.rstrip('/') + '/' + tag['href'].lstrip('/')
    return None


def scrape_email(url):
    if not url:
        return None, 'brak_strony'

    if is_facebook(url):
        return None, 'facebook'

    html = fetch_page(url)
    if not html:
        return None, 'blad_pobierania'

    emails = find_emails_in_html(html)
    if emails:
        return emails[0], 'strona_glowna'

    contact_url = find_contact_page_url(url, html)
    if contact_url:
        contact_html = fetch_page(contact_url)
        if contact_html:
            emails = find_emails_in_html(contact_html)
            if emails:
                return emails[0], 'strona_kontakt'

    base_url = url.rstrip('/')
    for slug in CONTACT_PAGE_SLUGS + LEGAL_PAGE_SLUGS:
        page_html = fetch_page(base_url + slug)
        if page_html:
            emails = find_emails_in_html(page_html)
            if emails:
                return emails[0], f'strona_{slug.strip("/")}'

    return None, 'nie_znaleziono'
