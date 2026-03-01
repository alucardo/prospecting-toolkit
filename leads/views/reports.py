import base64
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string

from leads.models import Lead, GoogleBusinessAnalysis
from leads.services.pdf_service import html_to_pdf


def _get_cover_image_base64() -> str:
    """Wczytuje okładkę i zwraca jako base64 string gotowy do img src."""
    cover_path = Path(settings.BASE_DIR) / "leads/static/leads/images/report_cover.jpg"
    image_bytes = cover_path.read_bytes()
    return base64.b64encode(image_bytes).decode("utf-8")

def _get_page_bg_base64() -> str:
    bg_path = Path(settings.BASE_DIR) / "leads/static/leads/images/page_background.jpg"
    return base64.b64encode(bg_path.read_bytes()).decode("utf-8")

def _get_logo_base64() -> str:
    logo_path = Path(settings.BASE_DIR) / "leads/static/leads/images/logo.jpg"
    return base64.b64encode(logo_path.read_bytes()).decode("utf-8")


DAY_ORDER = ['Pon', 'Wt', 'Sr', 'Czw', 'Pt', 'Sob', 'Nd']

def _get_context(pk: int) -> dict:
    """Wspólny kontekst dla preview i PDF."""
    lead = get_object_or_404(Lead, pk=pk)
    analysis = lead.business_analyses.first()

    hours_ordered = []
    if analysis and analysis.hours_data:
        for day in DAY_ORDER:
            if day in analysis.hours_data:
                hours_ordered.append((day, analysis.hours_data[day]))

    return {
        "analysis": analysis,
        "lead": lead,
        "hours_ordered": hours_ordered,
        "person": "Imie i nazwisko",
        "phone": "555 555 555",
        "mail": "kontakt@bsmarti.com",
        "cover_image_b64": _get_cover_image_base64(),
        "page_bg_b64": _get_page_bg_base64(),
        "logo_b64": _get_logo_base64(),
    }


def google_analysis_preview(request, pk):
    return render(request, "leads/reports/google_analysis.html", _get_context(pk))


def google_analysis_pdf(request, pk):
    context = _get_context(pk)
    html = render_to_string("leads/reports/google_analysis.html", context)
    pdf_bytes = html_to_pdf(html)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="audyt-{pk}.pdf"'
    return response


def audit_edit(request, pk):
    """Edycja ręcznych pól audytu."""
    lead = get_object_or_404(Lead, pk=pk)
    analysis = lead.business_analyses.first()  # najnowsza

    if not analysis:
        return redirect('leads:lead_detail', pk=pk)

    if request.method == 'POST':
        # has_menu: '' = nie sprawdzono, 'true' = tak, 'false' = nie
        has_menu_raw = request.POST.get('has_menu', '')
        has_social_raw = request.POST.get('has_social_media', '')

        analysis.has_menu = True if has_menu_raw == 'true' else (False if has_menu_raw == 'false' else None)
        analysis.has_social_media = True if has_social_raw == 'true' else (False if has_social_raw == 'false' else None)
        analysis.website_recommendations = request.POST.get('website_recommendations', '').strip()

        # custom_summary_items: każda linia to osobny punkt
        items_raw = request.POST.get('custom_summary_items', '').strip()
        analysis.custom_summary_items = [line.strip() for line in items_raw.splitlines() if line.strip()]

        # Rekomendacje AI można ręcznie poprawić
        analysis.name_recommendation = request.POST.get('name_recommendation', '').strip()
        analysis.description_recommendation = request.POST.get('description_recommendation', '').strip()

        analysis.save()
        return redirect('leads:audit_edit', pk=pk)

    return render(request, 'leads/reports/audit_edit.html', {
        'lead': lead,
        'analysis': analysis,
    })
