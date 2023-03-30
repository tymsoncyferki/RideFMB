from django.shortcuts import render
from wiki.models import *
from django.db.models import F


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
        riders_html = Rider.objects.filter(name__icontains=query)
        events_html = Event.objects.filter(name__icontains=query)
    else:
        riders_html = False
        events_html = False
    return render(request, 'wiki/search.html', {'riders': riders_html, 'events': events_html})


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

    # filtering
    country = request.GET.get('country')
    if country and country != 'all':
        all_riders = all_riders.filter(country__isocode=country)

    ranked = request.GET.get('ranked')
    if ranked and ranked != 'all':
        if ranked == 'yes':
            all_riders = all_riders.filter(active=True)
        else:
            all_riders = all_riders.filter(active=False)

    # sorting
    sort_option = request.GET.get('sort')
    if sort_option:
        if sort_option[0] == '-':
            sort = sort_option[1:]
            all_riders = all_riders.order_by(F(sort).desc(nulls_last=True))
        else:
            all_riders = all_riders.order_by(F(sort_option).asc(nulls_last=True))
    else:
        all_riders = all_riders.order_by('-alltime_points')

    # arguments
    sort_labels = ['Most all-time points', 'Least all-time points', 'Rank ascending', 'Rank descending', 'Medals',
                   'Gold medals', 'Silver medals', 'Bronze medals', 'Name']
    sort_queries = ['-alltime_points', 'alltime_points', 'rank', '-rank', '-medal', '-gold', '-silver', '-bronze',
                    'lastname']
    sort_options = list(zip(sort_labels, sort_queries))
    filter_labels = ['Name', 'Country', 'Sponsors', 'Ranked']
    url_params = ['sort', 'country', 'ranked']
    medals = ['-medal', '-gold', '-silver', '-bronze']
    countries = Country.objects.all().order_by('name')

    # page
    riders_html = all_riders[start_idx:last_idx]
    pages_count = (all_riders.count() // 20) + 1
    return render(request, 'wiki/riders.html', {'riders': riders_html, 'page_index': page_idx,
                                                'pages_count': pages_count, 'sortOptions': sort_options,
                                                'filterLabels': filter_labels, 'url_params': url_params,
                                                'medals': medals, 'countries': countries})


def event(request, event_id, slug):
    main_event = Event.objects.get(id=event_id)
    parts = main_event.participation_set.all().order_by('rank')
    return render(request, 'wiki/event.html', {'event': main_event, 'participations': parts})


def events(request, page_idx=1):
    start_idx = (page_idx - 1) * 10
    last_idx = start_idx + 30
    # events = Event.objects.all().order_by('-date')[start_idx:last_idx]
    events_html = Event.objects.all().order_by('-date')
    return render(request, 'wiki/events.html', {'events': events_html})


def schedule(request, year):
    events_html = Event.objects.filter(date__year=year).order_by('date')
    return render(request, 'wiki/schedule.html', {'events': events_html, 'year': year})


def ranking(request, page_idx):
    start_idx = (page_idx - 1) * 10
    last_idx = start_idx + 10
    riders_html = Rider.objects.filter(active=True).filter(rank__gt=0).order_by('rank')[start_idx:last_idx]
    return render(request, 'wiki/ranking.html', {'riders': riders_html, 'page_index': page_idx})
