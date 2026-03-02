from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from leads.models import UserContact


@login_required
def user_contact_edit(request):
    contact, _ = UserContact.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        contact.full_name = request.POST.get('full_name', '').strip()
        contact.position = request.POST.get('position', '').strip()
        contact.phone = request.POST.get('phone', '').strip()
        contact.email = request.POST.get('email', '').strip()

        if 'photo' in request.FILES:
            contact.photo = request.FILES['photo']

        contact.save()
        return redirect('leads:user_contact_edit')

    return render(request, 'leads/user_contact_edit.html', {
        'contact': contact,
    })
