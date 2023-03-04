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


def rider(request, rider_id, slug):
    main_rider = Rider.objects.get(id=rider_id)
    parts = main_rider.participation_set.all()
    return render(request, 'wiki/rider.html', {'rider': main_rider, 'participations': parts})


def event(request, event_id, slug):
    main_event = Event.objects.get(id=event_id)
    parts = main_event.participation_set.all()
    return render(request, 'wiki/event.html', {'event': main_event, 'participations': parts})
