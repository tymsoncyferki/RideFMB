from django.shortcuts import render
from wiki.models import *
import threading


def index(request):
    return render(request, 'wiki/index.html')


def rider(request, rider_id, slug):
    main_rider = Rider.objects.get(id=rider_id)
    parts = main_rider.participation_set.all()
    spons = main_rider.sponsorship_set.all()
    return render(request, 'wiki/rider.html', {'rider': main_rider, 'participations': parts, 'sponsorships': spons})


def search(request):
    query = request.GET.get('q')
    if query:
        riders = Rider.objects.filter(name__icontains=query)
        events = Event.objects.filter(name__icontains=query)
    else:
        riders = Rider.objects.all()
        events = Event.objects.all()
    return render(request, 'wiki/search.html', {'riders': riders, 'events': events})


def riders(request, page_idx=1):
    start_idx = (page_idx - 1) * 10
    last_idx = start_idx + 30
    riders = Rider.objects.all().order_by('-alltime_points')[start_idx:last_idx]
    return render(request, 'wiki/riders.html', {'results': riders})


def event(request, event_id, slug):
    main_event = Event.objects.get(id=event_id)
    parts = main_event.participation_set.all().order_by('rank')
    return render(request, 'wiki/event.html', {'event': main_event, 'participations': parts})


def events(request, page_idx=1):
    start_idx = (page_idx - 1) * 10
    last_idx = start_idx + 30
    # events = Event.objects.all().order_by('-date')[start_idx:last_idx]
    events = Event.objects.all().order_by('-date')
    return render(request, 'wiki/events.html', {'events': events})


def schedule(request, year):
    events = Event.objects.filter(year=year).order_by('date')
    return render(request, 'wiki/schedule.html', {'events': events, 'year': year})


def ranking(request, page_idx):
    start_idx = (page_idx - 1) * 10
    last_idx = start_idx + 10
    riders = Rider.objects.filter(active=True).filter(rank__gt=0).order_by('rank')[start_idx:last_idx]
    return render(request, 'wiki/ranking.html', {'riders': riders, 'page_index': page_idx})
