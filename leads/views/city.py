from django.shortcuts import render, redirect
from ..models import City
from ..forms import CityForm

def city_index(request):
    cities = City.objects.all()
    context = {
        'cities': cities,
    }
    return render(request, 'leads/city/index.html', context)


def city_create(request):
    form = CityForm()

    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leads:city_index')

    context = {
        'form': form,
    }
    return render(request, 'leads/city/new.html', context)


def city_detail(request, pk):
    city = City.objects.get(pk=pk)
    context = {
        'city': city,
    }
    return render(request, 'leads/city/detail.html', context)

def city_edit(request, pk):
    city = City.objects.get(pk=pk)
    form = CityForm(instance=city)

    if request.method == 'POST':
        form = CityForm(request.POST, instance=city)
        if form.is_valid():
            form.save()
            return redirect('leads:city_index')

    context = {
        'form': form,
        'city': city,
    }
    return render(request, 'leads/city/edit.html', context)


def city_delete(request, pk):
    city = City.objects.get(pk=pk)
    if request.method == 'POST':
        city.delete()
        return redirect('leads:city_index')
    return redirect('leads:city_index')