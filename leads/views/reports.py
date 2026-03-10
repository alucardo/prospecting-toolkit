import base64
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string

from leads.models import Lead, UserContact, VoivodeshipKeyword
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

def _get_photo_small_base64() -> str:
    photo_small_path = Path(settings.BASE_DIR) / "leads/static/leads/images/photo_small.jpg"
    return base64.b64encode(photo_small_path.read_bytes()).decode("utf-8")

def _get_photo_big_base64() -> str:
    photo_big_path = Path(settings.BASE_DIR) / "leads/static/leads/images/photo_big.jpg"
    return base64.b64encode(photo_big_path.read_bytes()).decode("utf-8")

def loga_base64():
    hs_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/hs.jpg"
    bh_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/bh.jpg"
    rw_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/rw.jpg"
    tb_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/tb.jpg"
    vino_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/vino.jpg"
    viet_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/viet.jpg"
    szym_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/szym.jpg"
    zac_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/zac.jpg"
    groj_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/groj.jpg"
    siesta_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/siesta.jpg"
    fish_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/fish.jpg"
    prosto_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/prosto.jpg"
    at_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/at.jpg"
    blis_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/blis.jpg"
    rob_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/rob.jpg"
    wcz_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/wcz.jpg"
    ex_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/ex.jpg"
    cze_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/cze.jpg"
    pizza_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/pizza.jpg"
    szlak_path = Path(settings.BASE_DIR) / "leads/static/leads/images/loga/szlak.jpg"
    return {
        "hs": base64.b64encode(hs_path.read_bytes()).decode("utf-8"),
        "bh": base64.b64encode(bh_path.read_bytes()).decode("utf-8"),
        "rw": base64.b64encode(rw_path.read_bytes()).decode("utf-8"),
        "tb": base64.b64encode(tb_path.read_bytes()).decode("utf-8"),
        "vino": base64.b64encode(vino_path.read_bytes()).decode("utf-8"),
        "viet": base64.b64encode(viet_path.read_bytes()).decode("utf-8"),
        "szym": base64.b64encode(szym_path.read_bytes()).decode("utf-8"),
        "zac": base64.b64encode(zac_path.read_bytes()).decode("utf-8"),
        "groj": base64.b64encode(groj_path.read_bytes()).decode("utf-8"),
        "siesta": base64.b64encode(siesta_path.read_bytes()).decode("utf-8"),
        "fish": base64.b64encode(fish_path.read_bytes()).decode("utf-8"),
        "prosto": base64.b64encode(prosto_path.read_bytes()).decode("utf-8"),
        "at": base64.b64encode(at_path.read_bytes()).decode("utf-8"),
        "blis": base64.b64encode(blis_path.read_bytes()).decode("utf-8"),
        "rob": base64.b64encode(rob_path.read_bytes()).decode("utf-8"),
        "wcz": base64.b64encode(wcz_path.read_bytes()).decode("utf-8"),
        "ex": base64.b64encode(ex_path.read_bytes()).decode("utf-8"),
        "cze": base64.b64encode(cze_path.read_bytes()).decode("utf-8"),
        "pizza": base64.b64encode(pizza_path.read_bytes()).decode("utf-8"),
        "szlak": base64.b64encode(szlak_path.read_bytes()).decode("utf-8"),
    }


DAY_ORDER = ['Pon', 'Wt', 'Sr', 'Czw', 'Pt', 'Sob', 'Nd']


def _annotate_keywords_with_volume(lead, keyword_volumes):
    """Zwraca frazy leada z dopisanym monthly_searches z voivodeship."""
    result = []
    for kw in lead.keywords_list.all().prefetch_related('rank_checks'):
        kw.monthly_searches = keyword_volumes.get(kw.phrase)
        result.append(kw)
    return result


def _get_context(request, pk: int) -> dict:
    """Wspólny kontekst dla preview i PDF."""
    lead = get_object_or_404(Lead, pk=pk)
    analysis = lead.business_analyses.first()
    contact, _ = UserContact.objects.get_or_create(user=request.user)

    hours_ordered = []
    if analysis and analysis.hours_data:
        for day in DAY_ORDER:
            if day in analysis.hours_data:
                hours_ordered.append((day, analysis.hours_data[day]))

    # Wolumeny fraz z województwa leada
    voivodeship = lead.city.voivodeship if lead.city else None
    keyword_volumes = {}
    if voivodeship:
        vkws = VoivodeshipKeyword.objects.filter(
            voivodeship=voivodeship,
            phrase__in=lead.keywords_list.values_list('phrase', flat=True)
        )
        keyword_volumes = {vkw.phrase: vkw.monthly_searches for vkw in vkws}

    # Zdjecie uzytkownika jako base64 (wymagane dla Playwright)
    contact_photo_b64 = None
    if contact.photo:
        contact_photo_b64 = base64.b64encode(contact.photo.read()).decode('utf-8')
        contact.photo.seek(0)  # reset po odczycie

    loga_b64 = loga_base64()

    return {
        "analysis": analysis,
        "lead": lead,
        "hours_ordered": hours_ordered,
        "person": "Imie i nazwisko",
        "phone": "555 555 555",
        "mail": "kontakt@bsmarti.com",
        "contact": contact,
        "contact_photo_b64": contact_photo_b64,
        "cover_image_b64": _get_cover_image_base64(),
        "page_bg_b64": _get_page_bg_base64(),
        "logo_b64": _get_logo_base64(),
        "photo_small_b64": _get_photo_small_base64(),
        "photo_big_b64": _get_photo_big_base64(),
        "keyword_volumes": keyword_volumes,
        "keywords_with_volume": _annotate_keywords_with_volume(lead, keyword_volumes),
        "loga_b64": loga_b64,
    }


def google_analysis_preview(request, pk):
    return render(request, "leads/reports/google_analysis.html", _get_context(request, pk))


def google_analysis_pdf(request, pk):
    context = _get_context(request, pk)
    html = render_to_string("leads/reports/google_analysis.html", context)
    pdf_bytes = html_to_pdf(html)
    lead_name = context['lead'].name

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Audyt {lead_name}.pdf"'
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

        # Checkbox: show_keyword_searches (obecny w POST = True, nieobecny = False)
        analysis.show_keyword_searches = 'show_keyword_searches' in request.POST

        analysis.save()
        return redirect('leads:audit_edit', pk=pk)

    return render(request, 'leads/reports/audit_edit.html', {
        'lead': lead,
        'analysis': analysis,
    })
