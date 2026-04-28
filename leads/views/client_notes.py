from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Lead
from ..forms import LeadNoteForm


@login_required
def client_notes_index(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    notes = lead.notes.all().order_by('-created_at')
    note_form = LeadNoteForm()

    return render(request, 'leads/client/notes.html', {
        'lead': lead,
        'notes': notes,
        'note_form': note_form,
    })
