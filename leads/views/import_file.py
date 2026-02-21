import pandas as pd
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from ..models import ImportFile, Lead
from ..forms import ImportFileForm


def clean_row(row):
    cleaned = {}
    for key, value in row.items():
        if isinstance(value, float) and math.isnan(value):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned

def normalize_address(address):
    if not address:
        return ''
    return address.split(',')[0].strip().lower()


@login_required
def import_upload(request):
    form = ImportFileForm()

    if request.method == 'POST':
        form = ImportFileForm(request.POST, request.FILES)
        if form.is_valid():
            import_file = form.save(commit=False)
            import_file.original_filename = request.FILES['file'].name
            import_file.save()
            return redirect('leads:import_map', pk=import_file.pk)

    context = {
        'form': form,
    }
    return render(request, 'leads/import/upload.html', context)


@login_required
def import_map(request, pk):
    import_file = get_object_or_404(ImportFile, pk=pk)

    df = pd.read_csv(import_file.file.path)
    columns = list(df.columns)

    lead_fields = [
        ('name', 'Nazwa'),
        ('phone', 'Telefon'),
        ('address', 'Adres (lub pierwsza część)'),
        ('address2', 'Adres - druga część (opcjonalnie)'),
        ('address3', 'Adres - trzecia część (opcjonalnie)'),
        ('email', 'Email'),
        ('website', 'Strona WWW'),
    ]

    if request.method == 'POST':
        mapping = {}
        for field, _ in lead_fields:
            col = request.POST.get(field)
            if col:
                mapping[field] = col

        created = 0
        skipped = 0

        for _, row in df.iterrows():
            name = str(row.get(mapping.get('name', ''), '')).strip()

            # Najpierw zbuduj adres
            address_parts = []
            for addr_field in ['address', 'address2', 'address3']:
                col = mapping.get(addr_field)
                if col:
                    value = row.get(col, '')
                    if not (isinstance(value, float) and math.isnan(value)) and value:
                        address_parts.append(str(value))
            address = ', '.join(address_parts)

            # Potem sprawdź duplikaty
            if Lead.objects.filter(
                    name__iexact=name,
                    city=import_file.city
            ).exists():
                existing = Lead.objects.filter(
                    name__iexact=name,
                    city=import_file.city
                )
                if any(normalize_address(l.address) == normalize_address(address) for l in existing):
                    skipped += 1
                    continue

            lead_data = {
                'city': import_file.city,
                'source': 'file',
                'address': address,
                'raw_data': clean_row(row.to_dict()),
            }

            for field, col in mapping.items():
                if field in ['address', 'address2', 'address3']:
                    continue
                value = row.get(col, '')
                lead_data[field] = '' if (isinstance(value, float) and math.isnan(value)) else value

            Lead.objects.create(**lead_data)
            created += 1

        import_file.delete()

        return render(request, 'leads/import/done.html', {
            'created': created,
            'skipped': skipped,
            'city': import_file.city,
        })

    context = {
        'import_file': import_file,
        'columns': columns,
        'lead_fields': lead_fields,
    }
    return render(request, 'leads/import/map.html', context)
