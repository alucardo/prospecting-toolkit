from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Lead, LeadNote
from ..forms import LeadNoteForm


@login_required
def lead_note_create(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.lead = lead
            note.save()
    return redirect('leads:lead_detail', pk=lead.pk)


@login_required
def lead_note_edit(request, pk, note_pk):
    lead = get_object_or_404(Lead, pk=pk)
    note = get_object_or_404(LeadNote, pk=note_pk, lead=lead)
    if request.method == 'POST':
        form = LeadNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            return redirect('leads:lead_detail', pk=lead.pk)
    else:
        form = LeadNoteForm(instance=note)
    return render(request, 'leads/lead/note_edit.html', {'form': form, 'lead': lead, 'note': note})


@login_required
def lead_note_delete(request, pk, note_pk):
    lead = get_object_or_404(Lead, pk=pk)
    note = get_object_or_404(LeadNote, pk=note_pk, lead=lead)
    if request.method == 'POST':
        note.delete()
    return redirect('leads:lead_detail', pk=lead.pk)
