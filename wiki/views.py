from django.shortcuts import render
from wiki.models import *


def index(request):
    return render(request, 'wiki/index.html')


def search(request):
    query = request.GET.get('q')
    if query:
        results = Rider.objects.filter(name__icontains=query)
    else:
        results = Rider.objects.all()

    return render(request, 'wiki/search.html', {'results': results})


def rider(request, rider_name, rider_id):
    rider = Rider.objects.get(id=rider_id)
    return render(request, 'wiki/rider.html', {'rider': rider})