from datetime import datetime
import requests
from bs4 import BeautifulSoup
from django.core.exceptions import *
from django.utils.text import slugify

from wiki.models import Rider, Event, Partner, Partnership, Participation, Series, Sponsor, Sponsorship, Country, getID


def updateRanking():
    """ Updates ranking points, rank, active field """
    # Getting main page
    Rider.objects.all().update(active=False)
    main_url = "https://www.fmbworldtour.com/ranking/?series=70"
    main_page = requests.get(main_url)
    main_soup = BeautifulSoup(main_page.text, 'html.parser')
    pages = main_soup.find('div', {'class': 'page-counter'})
    # Iterate through ranking pages
    for page in pages.find_all('a', {'class': 'page-counter-link'}):
        print('-----------')
        print('Scraping page...')
        # Get page content
        ranking_url = page.get('href')
        ranking_page = requests.get(ranking_url)
        ranking_soup = BeautifulSoup(ranking_page.text, 'html.parser')
        # Get ranking table
        ranking_table = ranking_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        # Iterate through riders on the page
        for rider_row in ranking_table.find_all('tr'):
            # Get rider ID
            rider_url = rider_row.find('a').get('href')
            rider_id = getID(rider_url)
            rider = Rider.objects.get(pk=rider_id)
            row_data = rider_row.find_all('td')
            print('-----')
            print('Scraping rider:', rider.name)
            # Get ranking data
            rider.rank = row_data[0].text.strip()
            rider.points = row_data[-2].text.strip()
            rider.active = True
            rider.save()
            print('rank', row_data[0].text.strip(), 'points', row_data[-2].text.strip())


def scrapeRiderInfo(rider_url=None, new_id=None, content=None):
    """ Scrapes basic information about rider (without sponsors, events, medals) """
    # getting id and url
    assert rider_url or new_id, 'specify rider_url or new_id'
    if not new_id:
        new_id = getID(rider_url)
    if not rider_url:
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + new_id
    # getting page content
    if content is None:
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'html.parser')
    else:
        rider_soup = content
    rider_info = rider_soup.find('div', {'class': 'athelte-profile'})  # not a mistake (athelte)
    # scraping basic info
    name = rider_info.find('h1').text.strip()
    namelist = name.split(' ')
    firstname = namelist[0]
    lastname = ' '.join(namelist[1:])
    slug = slugify(name)
    country_name = rider_info.find('small').text.strip()
    country = Country.getCountry(country_name)
    photo = rider_info.find('img').get('src')
    try:
        instagram = rider_info.find('svg', {'class': 'icon-instagram'}).parent.get('href')
    except (Exception,):
        instagram = ''
    # scraping rank
    rider_history = rider_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
    try:
        rank = rider_history.find('a', {'href': "https://www.fmbworldtour.com/ranking?series=70"}). \
            previous.previous_sibling.find('sup').previous_sibling
        active = True
    except (Exception,):
        rank = None
        active = False
    # saving rider
    try:
        rider = Rider.objects.get(id=new_id)
        rider.firstname = firstname
        rider.lastname = lastname
        rider.name = name
        rider.slug = slug
        rider.country = country
        rider.photo = photo
        rider.instagram = instagram
        rider.active = active
        rider.rank = rank
    except ObjectDoesNotExist:
        rider = Rider(id=new_id, firstname=firstname, lastname=lastname, name=name, slug=slug, country=country,
                      photo=photo, instagram=instagram, active=active, rank=rank)
    rider.save()
    rider.fixInstagram()
    return rider


def scrapeSponsors(rider, content=None):
    """ Scrapes riders sponsorships """
    # Get page content
    if content is None:
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + str(rider.id)
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'html.parser')
    else:
        rider_soup = content
    try:
        rider_sponsors = rider_soup.find('p', {'class': 'athlete-profile-sponsors'}).text.strip()
    except (Exception,):
        print('No sponsors')
        return
    # Extract sponsors
    sponsors = [sponsor.strip() for sponsor in rider_sponsors.split('|')]
    main = True
    print('Scraping rider sponsors...')
    # Iterate through sponsors
    for sponsor_name in sponsors:
        if sponsor_name == '':
            continue
        # Add sponsor
        if not Sponsor.objects.filter(name=sponsor_name).exists():
            s = Sponsor(name=sponsor_name)
            s.save()
        # Add sponsorship
        Sponsorship(rider=rider, sponsor=Sponsor.objects.get(name=sponsor_name),
                    main=main).save()
        # First sponsor is the main sponsor
        if main:
            main = False


def scrapeParticipations(rider, content=None):
    """ Scrapes riders participations """
    # Get page content
    if content is None:
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + str(rider.id)
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'html.parser')
    else:
        rider_soup = content
    # Get participations table
    rider_results = rider_soup.find('h2', text="Previous Results").find_next_sibling()
    rider_parts = rider_results.find('tbody')
    # Iterate over participations
    for row in rider_parts.find_all('tr'):
        # Get cells with data
        cells = row.find_all('td')
        comp_url = row.find('a').get('href')
        event_id = getID(comp_url)
        # Scrape only non-existing participations
        if Participation.objects.filter(rider__pk=rider.id, event__pk=event_id).exists():
            print('Participation exists')
            continue
        # Get participation data
        points = cells[-1].text.strip()
        try:
            rank = row.find('a').previous.previous_sibling.find('sup').previous_sibling
        except (Exception,):
            rank = None
        print('Scraping rider participations...')
        # Add event if it somehow does not exist in database
        if not Event.objects.filter(pk=event_id).exists():
            scrapeEvent(event_url=comp_url, status='Completed', date_str='01 Jan 2000')
        # Save participation
        p = Participation(rider=rider, event=Event.objects.get(id=event_id),
                          rank=rank, points=points)
        p.save()


def scrapeRider(rider_url=None, new_id=None):
    """ Scrapes all information about rider """
    # get id
    assert rider_url or new_id, 'specify rider_url or new_id'
    if not new_id:
        new_id = getID(rider_url)
    if not rider_url:
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + new_id
    # Get page
    rider_page = requests.get(rider_url)
    rider_soup = BeautifulSoup(rider_page.text, 'html.parser')
    # information
    print('1. Rider information')
    rider = scrapeRiderInfo(new_id=new_id, content=rider_soup)
    # sponsors
    print('2. Rider sponsors')
    Sponsorship.objects.filter(rider__id=new_id).delete()
    scrapeSponsors(rider=rider, content=rider_soup)
    # participations
    print('3. Rider participations')
    scrapeParticipations(rider=rider, content=rider_soup)
    # medals
    print('4. Rider medals')
    rider.updateMedals()


def getRidersFromEvent(event_url=None, content=None, update=True):
    """
    Scrapes riders from an event
    update - set update to False to omit existing riders
    """
    # Get page content
    if content is None:
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'html.parser')
    else:
        event_soup = content
    try:
        rider_table = event_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
    except (Exception,):
        print('no data about event')
        return
    # Iterate through riders
    for rider in rider_table.find_all('tr'):
        rider_url = rider.find('a').get('href')
        print('---')
        print('Scraping rider:', rider_url)
        rider_id = getID(rider_url)
        if not update:
            # Scrape only non-existing ones
            if Rider.objects.filter(pk=rider_id).exists():
                print('Already scraped')
                continue
        scrapeRider(rider_url, rider_id)


def scrapeAllRiders():
    """ Scrapes all riders by iterating through all events """
    # Get main page content
    main_url = "https://www.fmbworldtour.com/events/"
    main_page = requests.get(main_url)
    main_soup = BeautifulSoup(main_page.text, 'html.parser')
    year_panel = main_soup.find('div', {'class': 'page-counter'})
    # Iterate through year pages
    for year in year_panel.find_all('a'):
        year_url = year.get('href')
        print("----------")
        print("Scraping year:", year_url)
        # Get page content
        year_page = requests.get(year_url)
        year_soup = BeautifulSoup(year_page.text, 'html.parser')
        event_table = year_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        # Iterate through events from a given year
        for event in event_table.find_all('tr'):
            event_url = event.find('a').get('href')
            print("------")
            print("Scraping riders from event:", event_url)
            getRidersFromEvent(event_url)
        print("Year scraped succesfully!")
    print("SUCCESS!")


def scrapePartners(event, content=None):
    """
    Scrapes event partners
    content - page content can be given
    """
    if content is None:
        event_url = 'https://www.fmbworldtour.com/competition/?id=' + str(event.id)
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'html.parser')
    else:
        event_soup = content
    event_details = event_soup.find('div', {'class': 'competition-details'})
    event_partners = event_details.find('strong', text='Partners: ')
    all_partners = event_partners.next_sibling.text.strip()
    partners = [partner.strip() for partner in all_partners.split('|')]
    print('Scraping event partners...')
    # Iterate through partners
    for partner_name in partners:
        # Add partner
        if not Partner.objects.filter(name=partner_name).exists():
            p = Partner(name=partner_name)
            p.save()
        partner = Partner.objects.get(name=partner_name)
        # Add only non-existing partnerships
        if Partnership.objects.filter(event__pk=event.id, partner__pk=partner.id).exists():
            print('Partnership exists')
            continue
        # Add partnership
        pship = Partnership(event=event, partner=partner)
        pship.save()


def scrapeSeries(event, content=None):
    """
    Scrapes event series
    content - page content can be given
    """
    if content is None:
        event_url = 'https://www.fmbworldtour.com/competition/?id=' + str(event.id)
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'html.parser')
    else:
        event_soup = content
    event_info = event_soup.find('div', {'class': 'api-content'})
    event_history = event_info.find_all('div')[-1]
    # Iterate over events from the same series
    for comp in event_history.find_all('a'):
        try:
            # Get competition
            comp_url = comp.get('href')
            comp_id = getID(comp_url)
            competition = Event.objects.get(id=comp_id)
        except ObjectDoesNotExist:
            continue
        # If competition is not our main event and is already in some series, add our event to this series and return
        if competition.series and competition.id != event.id:
            s = competition.series
            event.series = s
            event.save()
            print('Added to series')
            return
    sname = event.cleanName()
    try:
        Series.objects.get(name=sname)
        print('Already added to series')
    except ObjectDoesNotExist:
        print('Series created')
        s = Series(name=sname)
        s.save()
        event.series = s
        event.save()


def scrapeEvent(event_url, status, date_str, include_parts=False):
    """
    Scrapes event from given url
    status - Upcoming, Completed, Canceled
    date_str - format example: 01 Jul 2023
    include_parts - set to true to scrape riders and participations
    """
    new_id = getID(event_url)
    date = datetime.strptime(date_str, '%d %b %Y').date()
    status = status
    # Get page content
    event_page = requests.get(event_url)
    event_soup = BeautifulSoup(event_page.text, 'html.parser')
    event_info = event_soup.find('div', {'class': 'api-content'})
    # Get event information
    name = event_info.find('h1').text.strip()
    slug = slugify(name)
    location = event_info.find('small').text.strip()
    comma = location.rfind(',')
    city = location[:comma].strip()
    country_name = location[comma + 1:].strip()
    country = Country.getCountry(country_name)
    # Get event details
    event_details = event_soup.find('div', {'class': 'competition-details'})
    event_category = event_details.find('strong', text='Category: ')
    category = event_category.next_sibling.text.strip()
    event_discipline = event_details.find('strong', text='Disipline: ')
    discipline = event_discipline.next_sibling.text.strip()
    if discipline == 'Unknown' and status == 'Completed':
        discipline = 'Freeride'
    event_prize = event_details.find('strong', text='Prize Money: ')
    prize = event_prize.next_sibling.text.strip()
    event_website = event_details.find('strong', text='Website: ')
    website = event_website.next_sibling.get('href')
    # Save event
    try:
        event = Event.objects.get(id=new_id)
        event.name = name
        event.slug = slug
        event.date = date
        event.city = city
        event.country = country
        event.category = category
        event.discipline = discipline
        event.status = status
        event.prize = prize
        event.website = website
    except ObjectDoesNotExist:
        event = Event(id=new_id, name=name, slug=slug, date=date, city=city, country=country,
                      category=category, discipline=discipline, status=status,
                      prize=prize, website=website)
    event.save()
    # Scrape partners
    scrapePartners(event, content=event_soup)
    # Scrape series
    scrapeSeries(event, content=event_soup)
    if include_parts:
        getRidersFromEvent(event_url=event_url, content=event_soup)


def scrapeEventsYear(year_url=None, year=None, update=True):
    """
    Scrapes events from whole year
    year_url - year page url
    year - url will be created for given year
    update - set update to false to omit already existing events
    """
    assert year_url or year, 'year_url or year should be given'
    if year:
        year_url = "https://www.fmbworldtour.com/events/?yr=" + str(year)
    # Get page content
    year_page = requests.get(year_url)
    year_soup = BeautifulSoup(year_page.text, 'html.parser')
    event_table = year_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
    # Iterate over events
    for event in event_table.find_all('tr'):
        cells = event.find_all('td')
        date = cells[0].text.strip()
        status = cells[-1].text.strip()
        event_url = event.find('a').get('href')
        if not update:
            curid = getID(event_url)
            # Omit existing events
            if Event.objects.filter(pk=curid).exists():
                print("Already scraped")
                continue
        print("Scraping event:", event_url)
        if update:
            scrapeEvent(event_url, status, date, include_parts=True)
        else:
            scrapeEvent(event_url, status, date)
    print("Year scraped succesfully!")


def scrapeAllEvents():
    """ Scrapes all events """
    main_url = "https://www.fmbworldtour.com/events/"
    main_page = requests.get(main_url)
    main_soup = BeautifulSoup(main_page.text, 'html.parser')
    year_panel = main_soup.find('div', {'class': 'page-counter'})
    # Iterates over years
    for year in year_panel.find_all('a'):
        year_url = year.get('href')
        print("Scraping year:", year_url)
        print("----------")
        scrapeEventsYear(year_url)
    print("SUCCESS!")


def scrapeAllSeries():
    events = Event.objects.all()
    for i, event in enumerate(events):
        print(i, event)
        scrapeSeries(event=event)


def fixCities():
    for event in Event.objects.all():
        print(f"---{event.name}")
        new_id = event.id
        event_url = "https://www.fmbworldtour.com/competition/?id=" + str(new_id)
        # Get page content
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'html.parser')
        event_info = event_soup.find('div', {'class': 'api-content'})
        location = event_info.find('small').text.strip()
        comma = location.rfind(',')
        city = location[:comma].strip()
        print(f"Old: {event.city}, New: {city}")
        event.city = city
        event.save()
