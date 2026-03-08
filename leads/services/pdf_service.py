from playwright.sync_api import sync_playwright


def html_to_pdf(html_content: str) -> bytes:
    """Generuje PDF z HTML używając Playwright."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html_content, wait_until="domcontentloaded")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                scale=0.75,
                margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            )
        finally:
            browser.close()
    return pdf_bytes
