import asyncio
from playwright.async_api import async_playwright


async def _html_to_pdf_async(html_content: str) -> bytes:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        pdf_bytes = await page.pdf(
            format="A4",
            print_background=True,
            margin={"top": "15mm", "bottom": "15mm", "left": "12mm", "right": "12mm"},
        )
        await browser.close()
    return pdf_bytes


def html_to_pdf(html_content: str) -> bytes:
    """Synchroniczny wrapper - wywołuj ten w widokach Django."""
    return asyncio.run(_html_to_pdf_async(html_content))