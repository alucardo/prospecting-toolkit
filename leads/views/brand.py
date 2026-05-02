from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import Lead, BrandProfile


FIELDS = [
    ('description', 'Opis marki', 'Krótki opis czym się zajmuje firma, co oferuje, jaka jest jej historia...'),
    ('tone_of_voice', 'Ton komunikacji', 'Jak marka mówi do odbiorców? Formalnie/nieformalnie, z humorem, poważnie...'),
    ('target_audience', 'Grupa docelowa', 'Kto jest głównym odbiorcą? Wiek, płeć, zainteresowania, potrzeby...'),
    ('usp', 'USP (unikalna propozycja wartości)', 'Co wyróżnia tę markę na rynku? Dlaczego klient powinien wybrać właśnie ją?'),
    ('brand_values', 'Wartości marki', 'Co jest ważne dla marki? Jakość, tradycja, innowacja, lokalność...'),
    ('competition', 'Konkurencja', 'Kto jest konkurentem? Czym się od nich odróżniamy?'),
    ('language_rules', 'Zasady językowe', 'Czy używamy "ty" czy "Pan/Pani"? Czy unikamy żargonu? Emoji tak/nie?'),
    ('keywords', 'Słowa kluczowe / frazy marki', 'Frazy które warto powtarzać w komunikacji, tagline, slogany...'),
    ('avoid', 'Czego unikać', 'Tematy, słowa, skojarzenia których nie chcemy w komunikacji marki...'),
    ('seasonality', 'Sezonowość / ważne daty', 'Święta, eventy, okresy promocyjne ważne dla tej branży...'),
    ('extra_notes', 'Dodatkowe notatki', 'Inne ważne informacje o marce, kontekst, historia...'),
]


@login_required
def brand_profile(request, lead_pk):
    lead = get_object_or_404(Lead, pk=lead_pk, status='client')
    profile, _ = BrandProfile.objects.get_or_create(lead=lead)

    if request.method == 'POST':
        for field, _, _ in FIELDS:
            setattr(profile, field, request.POST.get(field, '').strip())
        profile.save()
        return redirect('leads:brand_profile', lead_pk=lead.pk)

    return render(request, 'leads/brand/profile.html', {
        'lead': lead,
        'profile': profile,
        'fields': [
            (field, label, placeholder, getattr(profile, field))
            for field, label, placeholder in FIELDS
        ],
    })
