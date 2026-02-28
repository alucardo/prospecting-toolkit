from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from leads.models import Lead
from leads.services.pdf_service import html_to_pdf


def google_analysis_preview(request, pk):
    """Podgląd HTML w przeglądarce — do stylowania i testowania."""
    lead = get_object_or_404(Lead, pk=pk)

    return render(request, "leads/reports/google_analysis.html", {
        "lead": lead,
    })

def google_analysis_pdf(request, pk):
    lead = get_object_or_404(Lead, pk=pk)

    html = render_to_string("leads/reports/google_analysis.html", {
        "lead": lead,
    })

    pdf_bytes = html_to_pdf(html)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="analiza-{lead.pk}.pdf"'
    return response