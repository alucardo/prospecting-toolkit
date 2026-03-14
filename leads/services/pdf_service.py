import tempfile
import os
from playwright.sync_api import sync_playwright


def html_to_pdf(html_content: str) -> bytes:
    """Generuje PDF z HTML używając Playwright."""
    # Zapisujemy HTML do pliku tymczasowego — page.set_content() ma limit rozmiaru
    # przy dużej ilości base64 (loga, zdjęcia), co powoduje crash. page.goto(file://)
    # ładuje plik bezpośrednio bez tego limitu.
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
        f.write(html_content)
        tmp_path = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',  # kluczowe na serwerach z małym /dev/shm
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-default-apps',
                '--mute-audio',
                '--no-first-run',
            ])
            try:
                page = browser.new_page(viewport={"width": 794, "height": 1123})
                page.goto(f'file://{tmp_path}', wait_until="domcontentloaded")
                pdf_bytes = page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                )
            finally:
                browser.close()
    finally:
        os.unlink(tmp_path)

    return pdf_bytes
