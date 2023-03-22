from django.shortcuts import render
from wiki.models import *
import threading
from django.shortcuts import redirect


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
        riders = False
        events = False
    return render(request, 'wiki/search.html', {'riders': riders, 'events': events})


def riders(request):
    # default
    page_idx = request.GET.get('page')
    if page_idx:
        page_idx = int(page_idx)
    else:
        page_idx = 1
    start_idx = (page_idx - 1) * 20
    last_idx = start_idx + 20
    all_riders = Rider.objects.all()

    # sorting
    sortOption = request.GET.get('sort')
    if sortOption:
        all_riders = all_riders.order_by(sortOption)
    else:
        all_riders = Rider.objects.all().order_by('alltime_rank')

    # arguments
    sortLabels = ['Most all-time points', 'Least all-time points', 'Rank ascending',
                  'Rank descending', 'Most medals', 'Least medals']
    sortQueries = ['-alltime_points', 'alltime_points', 'rank', '-rank', 'medals-asc', 'medals-desc']
    sortOptions = list(zip(sortLabels, sortQueries))
    filterLabels = ['Name', 'Country', 'Sponsors', 'Ranked']
    urlParams = ['sort']
    # page
    riders = all_riders[start_idx:last_idx]
    pages_count = (all_riders.count() // 20) + 1
    return render(request, 'wiki/riders.html', {'riders': riders, 'page_index': page_idx, 'pages_count': pages_count,
                                                'sortOptions': sortOptions, 'filterLabels': filterLabels,
                                                'urlParams': urlParams})


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
