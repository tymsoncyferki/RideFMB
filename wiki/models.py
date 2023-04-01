from django.db import models
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from django.utils.text import slugify
from django.core.exceptions import *
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
        """ Scrapes all information about rider """
        # get id
        assert rider_url or new_id, 'specify rider_url or new_id'
        if not new_id:
            new_id = getID(rider_url)
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

    @staticmethod
    def scrapeRiderInfo(rider_url=None, new_id=None):
        """ Scrapes basic information about rider (without sponsors, events, medals) """
        # getting id and url
        assert rider_url or new_id, 'specify rider_url or new_id'
        if not new_id:
            new_id = getID(rider_url)
        if not rider_url:
            rider_url = "https://www.fmbworldtour.com/athlete/?id=" + new_id
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
        country = Country.getCountry(country_name)
        photo = rider_info.find('img').get('src')
        try:
            instagram = rider_info.find('svg', {'class': 'icon-instagram'}).parent.get('href')
        except (Exception,):
            instagram = ''
        # scraping rank
        rider_history = rider_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        try:
            rank = rider_history.find('a', {'href': "https://www.fmbworldtour.com/ranking?series=70"}).\
                previous.previous_sibling.find('sup').previous_sibling
            active = True
        except (Exception,):
            rank = None
            active = False
        # saving rider
        rider = Rider(id=new_id, firstname=firstname, lastname=lastname, name=name, slug=slug, country=country,
                      photo=photo, instagram=instagram, active=active, rank=rank)
        rider.save()
        return rider

    @staticmethod
    def updateRanking():
        """ Updates ranking points, rank, active field """
        # Getting main page
        Rider.objects.all().update(active=False)
        main_url = "https://www.fmbworldtour.com/ranking/?series=70"
        main_page = requests.get(main_url)
        main_soup = BeautifulSoup(main_page.text, 'lxml')
        pages = main_soup.find('div', {'class': 'page-counter'})
        # Iterate through ranking pages
        for page in pages.find_all('a', {'class': 'page-counter-link'}):
            print('-----------')
            print('Scraping page...')
            # Get page content
            ranking_url = page.get('href')
            ranking_page = requests.get(ranking_url)
            ranking_soup = BeautifulSoup(ranking_page.text, 'lxml')
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

    def updateMedals(self):
        """ Counts rider medals """
        # Set everything to 0
        golds = 0
        silvers = 0
        bronzes = 0
        parts = self.participation_set.all()
        self.alltime_points = 0
        points = 0
        # Add according to participations
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

    @staticmethod
    def countMedals():
        """ Counts medals for all riders """
        riders = Rider.objects.all()
        for i, rider in enumerate(riders):
            print(i, 'counting', rider.name)
            rider.updateMedals()

    @staticmethod
    def getRidersFromEvent(event_url, update=True):
        """
        Scrapes riders from an event
        update - set update to False to omit existing riders
        """
        # Get page content
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'lxml')
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
            Rider.scrapeRider(rider_url, rider_id)

    @staticmethod
    def scrapeAllRiders():
        """ Scrapes all riders by iterating through all events """
        # Get main page content
        main_url = "https://www.fmbworldtour.com/events/"
        main_page = requests.get(main_url)
        main_soup = BeautifulSoup(main_page.text, 'lxml')
        year_panel = main_soup.find('div', {'class': 'page-counter'})
        # Iterate through year pages
        for year in year_panel.find_all('a'):
            year_url = year.get('href')
            print("----------")
            print("Scraping year:", year_url)
            # Get page content
            year_page = requests.get(year_url)
            year_soup = BeautifulSoup(year_page.text, 'lxml')
            event_table = year_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
            # Iterate through events from a given year
            for event in event_table.find_all('tr'):
                event_url = event.find('a').get('href')
                print("------")
                print("Scraping riders from event:", event_url)
                Rider.getRidersFromEvent(event_url)
            print("Year scraped succesfully!")
        print("SUCCESS!")

    def scrapeSponsors(self):
        """ Scrapes riders sponsorships """
        # Get page content
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + str(self.id)
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'lxml')
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
            # Add sponsor
            if not Sponsor.objects.filter(name=sponsor_name).exists():
                s = Sponsor(name=sponsor_name)
                s.save()
            # Add sponsorship
            Sponsorship(rider=self, sponsor=Sponsor.objects.get(name=sponsor_name),
                        main=main).save()
            # First sponsor is the main sponsor
            if main:
                main = False

    def scrapeParticipations(self):
        """ Scrapews riders participations """
        # Get page content
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + str(self.id)
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'lxml')
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
            if Participation.objects.filter(rider__pk=self.id, event__pk=event_id).exists():
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
                Event.scrapeEvent(event_url=comp_url, status='Completed', date_str='01 Jan 2000')
            # Save participation
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
    partners = models.ManyToManyField('Partner', through='Partnership')
    riders = models.ManyToManyField('Rider', through='Participation')

    def __str__(self):
        return f"{self.name}, {self.date.year}"

    def scrapePartners(self, content=None):
        """
        Scrapes event partners
        content - page content can be given
        """
        if content is None:
            event_url = 'https://www.fmbworldtour.com/competition/?id=' + str(self.id)
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
            # Add partnership
            pship = Partnership(event=self, partner=Partner.objects.get(name=partner_name))
            pship.save()

    @staticmethod
    def fixEventWebsite():
        # TODO: fix links
        pass

    @staticmethod
    def fixStatus():
        # TODO: status - upcoming, completed, canceled
        pass

    # def completed(self):
    #     # TODO: change completed to status
    #     pass

    @staticmethod
    def scrapeEvent(event_url, status, date_str, include_parts=False):
        """
        Scrapes event from given url
        status - Upcoming, Completed, Canceled
        date_str - format example: 01 Jul 2023
        include_parts - set to true to scrape riders and participations
        """
        new_id = getID(event_url)
        date = datetime.strptime(date_str, '%d %b %Y').date()
        completed = status
        # Get page content
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'lxml')
        event_info = event_soup.find('div', {'class': 'api-content'})
        # Get event information
        name = event_info.find('h1').text.strip()
        location = event_info.find('small').text.strip()
        comma = location.rfind(',')
        city = location[:comma].strip()
        country_name = location[comma+1:].strip()
        country = Country.getCountry(country_name)
        # Get event details
        event_details = event_soup.find('div', {'class': 'competition-details'})
        event_category = event_details.find('strong', text='Category: ')
        category = event_category.next_sibling.text.strip()
        event_discipline = event_details.find('strong', text='Disipline: ')
        discipline = event_discipline.next_sibling.text.strip()
        if discipline == 'Unknown':
            discipline = 'Freeride'
        event_prize = event_details.find('strong', text='Prize Money: ')
        prize = event_prize.next_sibling.text.strip()
        event_website = event_details.find('strong', text='Website: ')
        website = event_website.next_sibling.get('href')
        # Save event
        event = Event(id=new_id, name=name, date=date, city=city, country=country,
                      category=category, discipline=discipline, completed=completed,
                      prize=prize, website=website)
        event.save()
        event.scrapePartners(content=event_soup)
        if include_parts:
            Rider.getRidersFromEvent(event_url)

    @staticmethod
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
        year_soup = BeautifulSoup(year_page.text, 'lxml')
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
                Event.scrapeEvent(event_url, status, date, include_parts=True)
            else:
                Event.scrapeEvent(event_url, status, date)
        print("Year scraped succesfully!")

    @staticmethod
    def scrapeAllEvents():
        """ Scrapes all events """
        main_url = "https://www.fmbworldtour.com/events/"
        main_page = requests.get(main_url)
        main_soup = BeautifulSoup(main_page.text, 'lxml')
        year_panel = main_soup.find('div', {'class': 'page-counter'})
        # Iterates over years
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
        """ Completes countries from given shortnames """
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

    @staticmethod
    def getCountry(name):
        try:
            country = Country.objects.get(shortname=name)
        except ObjectDoesNotExist:
            # Create a country if it's not in the database
            new_country = Country(shortname=name)
            new_country.save()
            country = new_country
        return country


class Series(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Partner(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name

    @staticmethod
    def fixPartners(arg):
        """
        Fixes same partners but differently written
        arg - string that all partners contain
        """
        arg_partners = Partner.objects.filter(name__icontains=arg)
        main_partner = arg_partners[0]
        for partner in arg_partners[1:]:
            for partnership in partner.partnership_set.all():
                partnership.partner = main_partner
                partnership.save()
            partner.delete()


class Partnership(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    partner = models.ForeignKey('Partner', on_delete=models.CASCADE)

    def __str__(self):
        return self.partner.name + ': ' + self.event.name


def getID(url):
    """ Extracts ID from url """
    id_index = url.index('=') + 1
    return url[id_index:]


def updateDatabase():
    Event.scrapeEventsYear(datetime.now().year)
