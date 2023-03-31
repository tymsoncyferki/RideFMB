from django.db import models
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from django.utils.text import slugify
from wiki.scripts.countries import *
import pycountry


class Rider(models.Model):
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=150, default='rider_name')
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=20, default='Unknown', blank=True)
    description = models.TextField(blank=True)
    photo = models.CharField(max_length=255, blank=True)
    instagram = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=False)
    rank = models.IntegerField(default=0, null=True)
    points = models.IntegerField(default=0)
    alltime_points = models.FloatField(default=0)
    medal = models.IntegerField(default=0)
    gold = models.IntegerField(default=0)
    silver = models.IntegerField(default=0)
    bronze = models.IntegerField(default=0)
    sponsors = models.ManyToManyField('Sponsor', through='Sponsorship')
    events = models.ManyToManyField('Event', through='Participation')

    def __str__(self):
        return self.name

    def getMainSponsor(self):
        return self.sponsorship_set.filter(main=True)[0].sponsor.name

    @staticmethod
    def scrapeRider(rider_url=None, new_id=None):
        # get id
        assert rider_url or new_id, 'specify rider_url or new_id'
        if not new_id:
            id_start_idx = rider_url.index('=') + 1
            new_id = rider_url[id_start_idx:]
        # information
        print('1. Rider information')
        rider = Rider.scrapeRiderInfo(new_id=new_id)
        # sponsors
        print('2. Rider sponsors')
        rider.scrapeSponsors()
        # participations
        print('3. Rider participations')
        rider.scrapeParticipations()
        # medals
        print('4. Rider medals')
        rider.updateMedals()

    # Scrapes basic information about rider (without sponsors, events, medals)
    @staticmethod
    def scrapeRiderInfo(rider_url=None, new_id=None):
        # getting id
        assert rider_url or new_id, 'specify rider_url or new_id'
        if not new_id:
            id_start_idx = rider_url.index('=') + 1
            new_id = rider_url[id_start_idx:]

        # getting page content
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'lxml')
        rider_info = rider_soup.find('div', {'class': 'athelte-profile'})

        # scraping basic info
        name = rider_info.find('h1').text.strip()
        namelist = name.split(' ')
        firstname = namelist[0]
        lastname = ' '.join(namelist[1:])
        slug = slugify(name)
        country_name = rider_info.find('small').text.strip()
        country = Country.objects.get(shortname=country_name)
        photo = rider_info.find('img').get('src')
        try:
            instagram = rider_info.find('svg', {'class': 'icon-instagram'}).parent.get('href')
        except Exception:
            instagram = ''

        # scraping rank
        rider_history = rider_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        try:
            rank = rider_history.find('a', {'href': "https://www.fmbworldtour.com/ranking?series=70"}).\
                previous.previous_sibling.find('sup').previous_sibling
            active = True
        except Exception:
            rank = None
            active = False

        # saving rider
        rider = Rider(id=new_id, firstname=firstname, lastname=lastname, name=name, slug=slug, country=country, phoyo=photo,
                      instagram=instagram, active=active, rank=rank)
        rider.save()
        return rider

    # Updates ranking points, rank, active field
    @staticmethod
    def updateRanking():
        Rider.objects.all().update(active=False)
        main_url = "https://www.fmbworldtour.com/ranking/?series=70"
        main_page = requests.get(main_url)
        main_soup = BeautifulSoup(main_page.text, 'lxml')
        pages = main_soup.find('div', {'class': 'page-counter'})
        for page in pages.find_all('a', {'class': 'page-counter-link'}):
            print('-----------')
            print('scraping page...')
            ranking_url = page.get('href')
            ranking_page = requests.get(ranking_url)
            ranking_soup = BeautifulSoup(ranking_page.text, 'lxml')
            ranking_table = ranking_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
            for rider_row in ranking_table.find_all('tr'):
                rider_url = rider_row.find('a').get('href')
                id_start_index = rider_url.index('=') + 1
                rider_id = rider_url[id_start_index:]
                rider = Rider.objects.get(pk=rider_id)
                row_data = rider_row.find_all('td')
                print('-----')
                print('scraping rider:', rider.name)
                rider.rank = row_data[0].text.strip()
                rider.points = row_data[-2].text.strip()
                rider.active = True
                rider.save()
                print('rank', row_data[0].text.strip(), 'points', row_data[-2].text.strip())

    # Count rider medals
    def updateMedals(self):
        golds = 0
        silvers = 0
        bronzes = 0
        parts = self.participation_set.all()
        self.alltime_points = 0
        points = 0
        for part in parts:
            if part.rank == 1:
                golds += 1
            elif part.rank == 2:
                silvers += 1
            elif part.rank == 3:
                bronzes += 1
            points += part.points
        self.alltime_points = points
        self.gold = golds
        self.silver = silvers
        self.bronze = bronzes
        self.medal = golds + silvers + bronzes
        self.save()

    # Counts medals for all riders
    @staticmethod
    def countMedals():
        riders = Rider.objects.all()
        n = 0
        for rider in riders:
            print(n, 'counting', rider.name)
            n += 1
            rider.updateMedals()

    @staticmethod
    def scrapeRidersEvent(event_url):
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'lxml')
        try:
            rider_table = event_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        except Exception:
            print('no data about event')
            return
        for rider in rider_table.find_all('tr'):
            rider_url = rider.find('a').get('href')
            print('---')
            print('Scraping rider:', rider_url)
            id_start_index = rider_url.index('=') + 1
            rider_id = rider_url[id_start_index:]
            if Rider.objects.filter(pk=rider_id).exists():
                print('Already scraped')
                continue
            r = Rider.scrapeRider(rider_url)
            r.save()
            print('Scraping his participations...')
            Participation.scrapeParticipations(rider_url)

    @staticmethod
    def scrapeAllRiders():
        main_url = "https://www.fmbworldtour.com/events/"
        main_page = requests.get(main_url)
        main_soup = BeautifulSoup(main_page.text, 'lxml')
        year_panel = main_soup.find('div', {'class': 'page-counter'})
        for year in year_panel.find_all('a'):
            year_url = year.get('href')
            print("----------")
            print("Scraping year:", year_url)
            print("----------")
            year_page = requests.get(year_url)
            year_soup = BeautifulSoup(year_page.text, 'lxml')
            event_table = year_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
            for event in event_table.find_all('tr'):
                event_url = event.find('a').get('href')
                print("------")
                print("Scraping riders from event:", event_url)
                Rider.scrapeRidersEvent(event_url)
            print("Year scraped succesfully!")
        print("SUCCESS!")

    def scrapeSponsors(self):
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + str(self.id)
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'lxml')
        try:
            rider_sponsors = rider_soup.find('p', {'class': 'athlete-profile-sponsors'}).text.strip()
        except Exception:
            print('No sponsors')
            return
        sponsors = [sponsor.strip() for sponsor in rider_sponsors.split('|')]
        main = True
        print('Scraping rider sponsors...')
        for sponsor_name in sponsors:
            if not Sponsor.objects.filter(name=sponsor_name).exists():
                s = Sponsor(name=sponsor_name)
                s.save()
            Sponsorship(rider=self, sponsor=Sponsor.objects.get(name=sponsor_name),
                        main=main).save()
            if main:
                main = False

    def scrapeParticipations(self):
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + str(self.id)
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'lxml')
        rider_results = rider_soup.find('h2', text="Previous Results").find_next_sibling()
        rider_parts = rider_results.find('tbody')
        for row in rider_parts.find_all('tr'):
            cells = row.find_all('td')
            points = cells[-1].text.strip()
            comp_url = row.find('a').get('href')
            compid_start_index = comp_url.index('=') + 1
            event_id = comp_url[compid_start_index:]
            try:
                rank = row.find('a').previous.previous_sibling.find('sup').previous_sibling
            except Exception:
                rank = None
            if Participation.objects.filter(rider__pk=self.id, event__pk=event_id).exists():
                print('Participation exists')
                continue
            print('Scraping rider participations...')
            if not Event.objects.filter(pk=event_id).exists():
                e = Event.scrapeEvent(status='Completed', date_str='01 Jan 2000', event_url=comp_url)
                e.save()
            p = Participation(rider=Rider.objects.get(id=self.id), event=Event.objects.get(id=event_id),
                              rank=rank, points=points)
            p.save()


class Event(models.Model):
    name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=150, default='event_name')
    date = models.DateField(null=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    category = models.CharField(max_length=100, blank=True)
    discipline = models.CharField(max_length=100, blank=True)
    completed = models.BooleanField(default=True)
    prize = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)
    partners = models.TextField(blank=True)
    riders = models.ManyToManyField('Rider', through='Participation')

    def __str__(self):
        return f"{self.name}, {self.date.year}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Event, self).save(*args, **kwargs)

    @staticmethod
    def fixSlugs():
        events = Event.objects.all()
        n = events.count()
        for event in events:
            print(n, event.name)
            event.slug = slugify(event.name)
            event.save()
            n -= 1

    @staticmethod
    def fixEventWebsite():
        # TODO: wywalić http
        pass

    @staticmethod
    def scrapeEvent(status, date_str, event_url):
        id_start_index = event_url.index('=') + 1
        new_id = event_url[id_start_index:]
        date = datetime.strptime(date_str, '%d %b %Y').date()
        year = date.year
        completed = True
        if status == 'Upcoming':
            completed = False

        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'lxml')
        event_info = event_soup.find('div', {'class': 'api-content'})
        name = event_info.find('h1').text.strip()
        location = event_info.find('small').text.strip()
        comma = location.rfind(',')
        city, country = location[:comma].strip(), location[comma+1:].strip()

        event_details = event_soup.find('div', {'class': 'competition-details'})
        event_category = event_details.find('strong', text='Category: ')
        category = event_category.next_sibling.text.strip()
        event_discipline = event_details.find('strong', text='Disipline: ')
        discipline = event_discipline.next_sibling.text.strip()
        event_prize = event_details.find('strong', text='Prize Money: ')
        prize = event_prize.next_sibling.text.strip()
        event_website = event_details.find('strong', text='Website: ')
        website = event_website.next_sibling.get('href')
        event_partners = event_details.find('strong', text='Partners: ')
        partners = event_partners.next_sibling.text.strip()

        event = Event(id=new_id, name=name, date=date, year=year, city=city, country=country,
                      category=category, discipline=discipline, completed=completed,
                      prize=prize, website=website, partners=partners)
        return event

    @staticmethod
    def scrapeEventsYear(year_url):
        year_page = requests.get(year_url)
        year_soup = BeautifulSoup(year_page.text, 'lxml')
        event_table = year_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        for event in event_table.find_all('tr'):
            cells = event.find_all('td')
            date = cells[0].text.strip()
            status = cells[-1].text.strip()
            event_url = event.find('a').get('href')
            id_start_index = event_url.index('=') + 1
            curid = event_url[id_start_index:]
            if Event.objects.filter(pk=curid).exists():
                continue
            print("Scraping event:", event_url)
            e = Event.scrapeEvent(status, date, event_url)
            e.save()
        print("Year scraped succesfully!")

    @staticmethod
    def scrapeAllEvents():
        main_url = "https://www.fmbworldtour.com/events/"
        main_page = requests.get(main_url)
        main_soup = BeautifulSoup(main_page.text, 'lxml')
        year_panel = main_soup.find('div', {'class': 'page-counter'})
        for year in year_panel.find_all('a'):
            year_url = year.get('href')
            print("Scraping year:", year_url)
            print("----------")
            Event.scrapeEventsYear(year_url)
        print("SUCCESS!")


class Sponsor(models.Model):
    name = models.CharField(max_length=150, blank=True)
    riders = models.ManyToManyField('Rider', through='Sponsorship')

    def __str__(self):
        name = str(self.name)
        return name


class Participation(models.Model):
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    rank = models.IntegerField(default=None, blank=True)
    points = models.FloatField(default=0, blank=True)

    def __str__(self):
        return str(self.rank) + '. ' + self.rider.name + ', ' + \
            self.event.name + ' ' + str(self.event.date.year)


class Sponsorship(models.Model):
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE)
    sponsor = models.ForeignKey('Sponsor', on_delete=models.CASCADE)
    main = models.BooleanField(default=False)

    def __str__(self):
        return self.rider.name + ', ' + self.sponsor.name


class Country(models.Model):
    name = models.CharField(max_length=50, blank=True)
    shortname = models.CharField(max_length=5, blank=True)
    isocode = models.CharField(max_length=3, blank=True)
    photo = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.name + ', ' + self.isocode

    @staticmethod
    def createCountries():
        countries = Country.objects.all()
        for country in countries:
            isocode = country_codes[country.shortname]
            country.isocode = isocode
            c = pycountry.countries.get(alpha_2=isocode)
            country.name = c.name
            photo = "https://www.countryflagicons.com/FLAT/24/" + isocode + ".png"
            country.photo = photo
            print(country)
            country.save()


class Series(models.Model):
    name = models.CharField(max_length=50)

