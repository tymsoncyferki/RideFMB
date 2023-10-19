from django.shortcuts import render, get_object_or_404, redirect
from wiki.models import *
from django.db.models import F, Count, Q, Subquery, OuterRef, Avg
from django.utils.timezone import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout


def index(request):
    data = AppData.objects.get(id=1)
    upcoming_events = Event.objects.all().filter(date__year=datetime.now().year).filter(status='Upcoming').order_by(
        'date')[:5]
    top_riders = Rider.objects.filter(active=True).annotate(
        avg_rank=Subquery(
            Participation.objects.filter(
                rider__pk=OuterRef('pk')
            ).filter(event__date__gt='2021-01-01').order_by('-event__date').values('rank')[:3].annotate(
                avg=Avg('rank')).values('avg')
        )
    ).annotate(
        part_count=Subquery(
            Participation.objects.filter(
                rider__pk=OuterRef('pk')
            ).filter(event__date__gt='2021-01-01').values('rank').annotate(count=Count('*')).values('count')
        )
    ).filter(part_count__gt=2).order_by('avg_rank')[:5]

    return render(request, 'wiki/index.html', {'appData': data, 'events': upcoming_events, 'riders': top_riders})


def help_view(request):
    return render(request, 'wiki/help.html')


def contact(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        title = 'Contact form: ' + subject
        content = f'Email:\n{email}\n\n' \
                  f'Message:\n{message}'
        send_mail(title, content, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER])
        send_mail(
            'Contact request - RideFMB',
            f"Thanks for reaching out! We will try to respond to you as fast as possible.\n\n"
            f"RideFMB Team 2023\n\n",
            settings.EMAIL_HOST_USER,
            [email]
        )
        return redirect('wiki:success')
    return render(request, 'wiki/contact.html')


def success(request):
    return render(request, 'wiki/utils/success.html')


def about(request):
    return render(request, 'wiki/about.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST["uname"]
        password = request.POST["psw"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('wiki:account')
        else:
            return redirect('wiki:login')
    if request.user.is_authenticated:
        return redirect('wiki:account')
    else:
        return render(request, 'wiki/registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('wiki:login')


def account(request):
    if request.user.is_authenticated:
        username = request.user.username
        email = request.user.email
        return render(request, 'wiki/registration/account.html', {"username": username, "email": email})
    else:
        return redirect('wiki:login')


def search(request):
    query = request.GET.get('q')
    if query:
        riders_html = Rider.objects.filter(name__icontains=query)
        events_html = Event.objects.filter(name__icontains=query).order_by('-date')
    else:
        riders_html = False
        events_html = False
    return render(request, 'wiki/search.html', {'riders': riders_html, 'events': events_html})


def schedule(request, year):
    events_html = Event.objects.filter(date__year=year).order_by('date')
    return render(request, 'wiki/events/schedule.html', {'events': events_html, 'year': year})


def ranking(request, page_idx):
    start_idx = (page_idx - 1) * 10
    last_idx = start_idx + 10
    riders_html = Rider.objects.filter(active=True).filter(rank__gt=0).order_by('rank')[start_idx:last_idx]
    return render(request, 'wiki/riders/ranking.html', {'riders': riders_html, 'page_index': page_idx})


def rider(request, rider_id, slug):
    main_rider = get_object_or_404(Rider, id=rider_id)
    parts = main_rider.participation_set.all().order_by('-event__date')
    spons = main_rider.sponsorship_set.all()
    sources = main_rider.source_set.all()
    years = []
    for part in parts:
        if part.event.date.year not in years:
            years.append(part.event.date.year)
    return render(request, 'wiki/riders/rider.html',
                  {'rider': main_rider, 'participations': parts, 'sponsorships': spons,
                   'sources': sources, 'years': years})


def event(request, event_id, slug):
    main_event = get_object_or_404(Event, id=event_id)
    partnerships = main_event.partnership_set.all()
    parts = main_event.participation_set.all().order_by('rank')
    parts_women = main_event.participation_set.filter(rider__sex='Female').order_by('rank')
    parts_men = main_event.participation_set.filter(~Q(rider__sex='Female')).order_by('rank')
    try:
        series = main_event.series.event_set.all().order_by('-date')
    except AttributeError:
        series = [main_event]
    return render(request, 'wiki/events/event.html', {'event': main_event, 'participations': parts, 'series': series,
                                                      'partnerships': partnerships, "parts_men": parts_men,
                                                      "parts_women": parts_women})


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

    sex = request.GET.get('sex')
    if sex and sex != 'all':
        all_riders = all_riders.filter(sex=sex)

    sponsor = request.GET.get('sponsor')
    if sponsor and sponsor != 'all':
        all_riders = all_riders.filter(sponsor__id=sponsor)

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
    url_params = ['sort', 'country', 'ranked', 'sponsor']
    medals = ['-medal', '-gold', '-silver', '-bronze']
    countries = Country.objects.all().order_by('name')
    sponsors = Sponsor.objects.all().order_by('name')

    # page
    riders_html = all_riders[start_idx:last_idx]
    pages_count = (all_riders.count() // 20) + 1
    return render(request, 'wiki/riders/riders.html', {'riders': riders_html, 'page_index': page_idx,
                                                       'pages_count': pages_count, 'sortOptions': sort_options,
                                                       'filterLabels': filter_labels, 'url_params': url_params,
                                                       'medals': medals, 'countries': countries, 'sponsors': sponsors})


def events(request):
    # default
    page_idx = request.GET.get('page')
    if page_idx:
        page_idx = int(page_idx)
    else:
        page_idx = 1
    start_idx = (page_idx - 1) * 20
    last_idx = start_idx + 20
    all_events = Event.objects.all()

    # filtering
    country = request.GET.get('country')
    if country and country != 'all':
        all_events = all_events.filter(country__isocode=country)

    status = request.GET.get('status')
    if status and status != 'all':
        all_events = all_events.filter(status=status)

    partner = request.GET.get('partner')
    if partner and partner != 'all':
        all_events = all_events.filter(partnership__partner__id=partner)

    year = request.GET.get('year')
    if year and year != 'all':
        all_events = all_events.filter(date__year=year)

    series = request.GET.get('series')
    if series and series != 'all':
        all_events = all_events.filter(series__id=series)

    category = request.GET.get('category')
    if category and category != 'all':
        all_events = all_events.filter(category=category)

    discipline = request.GET.get('discipline')
    if discipline and discipline != 'all':
        all_events = all_events.filter(discipline=discipline)

    # sorting
    sort_option = request.GET.get('sort')
    if sort_option:
        if sort_option[0] == '-':
            sort = sort_option[1:]
            all_events = all_events.order_by(F(sort).desc(nulls_last=True))
        else:
            all_events = all_events.order_by(F(sort_option).asc(nulls_last=True))
    else:
        all_events = all_events.order_by('-date')

    # arguments
    sort_labels = ['Date descending', 'Date ascending', 'Name']
    sort_queries = ['-date', 'date', 'name']
    sort_options = list(zip(sort_labels, sort_queries))
    url_params = ['sort', 'country', 'status', 'partner', 'date', 'series']
    countries = Country.objects.all().order_by('name')
    partners = Partner.objects.all().order_by('name')
    seriess = Series.objects.annotate(event_count=Count('event')).filter(event_count__gt=1).order_by('name')

    # page
    events_html = all_events[start_idx:last_idx]
    pages_count = (all_events.count() // 20) + 1
    return render(request, 'wiki/events/events.html', {'events': events_html, 'page_index': page_idx,
                                                       'pages_count': pages_count, 'sortOptions': sort_options,
                                                       'seriess': seriess, 'url_params': url_params,
                                                       'countries': countries, 'partners': partners})


def handler_404(request, exception=None, template_name='wiki/utils/404.html'):
    return render(request, template_name, status=404)


def handler_500(request, exception=None, template_name='wiki/utils/505.html'):
    return render(request, template_name, status=500)
