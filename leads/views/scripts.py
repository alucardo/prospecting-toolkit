from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from ..models import CallScript, CallLog


@login_required
def script_index(request):
    scripts = CallScript.objects.annotate(
        total=Count('call_logs'),
        with_next_contact=Count('call_logs', filter=Q(call_logs__next_contact_date__isnull=False)),
    )

    rows = []
    for s in scripts:
        if s.total > 0:
            effectiveness = round(s.with_next_contact / s.total * 100)
        else:
            effectiveness = None
        rows.append({
            'script': s,
            'total': s.total,
            'with_next_contact': s.with_next_contact,
            'effectiveness': effectiveness,
        })

    return render(request, 'leads/scripts/index.html', {'rows': rows})


@login_required
def script_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        content = request.POST.get('content', '').strip()
        if name and content:
            CallScript.objects.create(name=name, content=content)
        return redirect('leads:script_index')
    return render(request, 'leads/scripts/form.html', {'script': None})


@login_required
def script_edit(request, pk):
    script = get_object_or_404(CallScript, pk=pk)
    if request.method == 'POST':
        script.name = request.POST.get('name', '').strip()
        script.content = request.POST.get('content', '').strip()
        script.is_active = 'is_active' in request.POST
        script.save()
        return redirect('leads:script_index')
    return render(request, 'leads/scripts/form.html', {'script': script})


@login_required
def script_delete(request, pk):
    script = get_object_or_404(CallScript, pk=pk)
    if request.method == 'POST':
        script.delete()
    return redirect('leads:script_index')


@login_required
def script_detail(request, pk):
    script = get_object_or_404(CallScript, pk=pk)
    logs = (
        script.call_logs
        .select_related('lead', 'lead__city')
        .order_by('-called_at')[:50]
    )
    total = script.call_logs.count()
    with_next = script.call_logs.filter(next_contact_date__isnull=False).count()
    effectiveness = round(with_next / total * 100) if total else None

    return render(request, 'leads/scripts/detail.html', {
        'script': script,
        'logs': logs,
        'total': total,
        'with_next': with_next,
        'effectiveness': effectiveness,
    })
