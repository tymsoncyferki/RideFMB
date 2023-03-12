from django.db import models
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from django.utils.text import slugify


class Rider(models.Model):
    name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=150, default='rider_name')
    nationality = models.CharField(max_length=50, blank=True)
    birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=20, default='Unknown', blank=True)
    description = models.TextField(blank=True)
    sponsors = models.ManyToManyField('Sponsor', through='Sponsorship')
    photo = models.CharField(max_length=255, blank=True)
    instagram = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=False)
    rank = models.IntegerField(default=0, null=True)
    points = models.IntegerField(default=0)
    alltime_points = models.FloatField(default=0)
    gold = models.IntegerField(default=0)
    silver = models.IntegerField(default=0)
    bronze = models.IntegerField(default=0)
    events = models.ManyToManyField('Event', through='Participation')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Rider, self).save(*args, **kwargs)

    @staticmethod
    def fixSlugs():
        riders = Rider.objects.all()
        n = riders.count()
        for rider in riders:
            print(n, rider.name)
            rider.slug = slugify(rider.name)
            rider.save()
            n -= 1

    @staticmethod
    def fixNames():
        riders = Rider.objects.all()
        n = riders.count()
        for rider in riders:
            print(n, rider.name)
            rider.name = rider.slug.replace("-", " ").title()
            rider.save()
            n -= 1

    @staticmethod
    def countMedals():
        riders = Rider.objects.all()
        n = riders.count()
        for rider in riders:
            print(n, rider.name)
            parts = rider.participation_set.all()
            for part in parts:
                if part.rank == 1:
                    rider.gold += 1
                elif part.rank == 2:
                    rider.silver += 1
                elif part.rank == 3:
                    rider.bronze += 1
                rider.alltime_points += part.points
            rider.save()
            n -= 1

    @staticmethod
    def scrapeRanking():
        # TODO: przejść po rankingu i zebrać pozycje i punkty
        pass

    @staticmethod
    def scrapeRider(rider_url):
        id_start_index = rider_url.index('=') + 1
        newid = rider_url[id_start_index:]
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'lxml')
        rider_info = rider_soup.find('div', {'class': 'athelte-profile'})
        name = rider_info.find('h1').text.strip()
        nationality = rider_info.find('small').text.strip()
        photo = rider_info.find('img').get('src')
        try:
            instagram = rider_info.find('svg', {'class': 'icon-instagram'}).parent.get('href')
        except:
            instagram = ''
        rider_history = rider_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        try:
            rank = rider_history.find('a', {'href': "https://www.fmbworldtour.com/ranking?series=70"}). \
                previous.previous_sibling.find('sup').previous_sibling
            active = True
        except:
            rank = None
            active = False

        rider = Rider(id=newid, name=name, nationality=nationality, photo=photo,
                      instagram=instagram, active=active, rank=rank)
        return rider

    @staticmethod
    def scrapeRidersEvent(event_url):
        event_page = requests.get(event_url)
        event_soup = BeautifulSoup(event_page.text, 'lxml')
        try:
            rider_table = event_soup.find('table', {'class': 'series-ranking-table'}).find('tbody')
        except:
            print('not data about event')
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
            if year_url == "https://www.fmbworldtour.com/events/?yr=2023":
                print('ommiting year...')
                continue
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


class Event(models.Model):
    name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=150, default='event_name')
    date = models.DateField(null=True)
    year = models.IntegerField(null=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    discipline = models.CharField(max_length=100, blank=True)
    completed = models.BooleanField(default=True)
    prize = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)
    partners = models.TextField(blank=True)
    riders = models.ManyToManyField('Rider', through='Participation')

    def __str__(self):
        return f"{self.name}, {self.year}"

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Event, self).save(*args, **kwargs)

    @staticmethod
    def fixEventWebsite():
        # TODO: wywalić http
        pass

    @staticmethod
    def scrapeEvent(status, date_str, event_url):
        id_start_index = event_url.index('=') + 1
        newid = event_url[id_start_index:]
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

        event = Event(id=newid, name=name, date=date, year=year, city=city, country=country,
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
            self.event.name + ' ' + str(self.event.year)

    @staticmethod
    def scrapeParticipations(rider_url):
        id_start_index = rider_url.index('=') + 1
        rider_id = rider_url[id_start_index:]
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
            except:
                rank = None
            if Participation.objects.filter(rider__pk=rider_id, event__pk=event_id).exists():
                continue
            if not Event.objects.filter(pk=event_id).exists():
                e = Event.scrapeEvent(status='Completed', date_str='01 Jan 2000', event_url=comp_url)
                e.save()
            p = Participation(rider=Rider.objects.get(id=rider_id), event=Event.objects.get(id=event_id),
                              rank=rank, points=points)
            p.save()


class Sponsorship(models.Model):
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE)
    sponsor = models.ForeignKey('Sponsor', on_delete=models.CASCADE)
    main = models.BooleanField(default=False)

    def __str__(self):
        return self.rider.name + ', ' + self.sponsor.name

    @staticmethod
    def scrapeSponsors(rider_id):
        rider_url = "https://www.fmbworldtour.com/athlete/?id=" + str(rider_id)
        rider_page = requests.get(rider_url)
        rider_soup = BeautifulSoup(rider_page.text, 'lxml')
        try:
            rider_sponsors = rider_soup.find('p', {'class':'athlete-profile-sponsors'}).text.strip()
        except:
            return
        sponsors = [sponsor.strip() for sponsor in rider_sponsors.split('|')]
        main = True
        print('Scraping rider sponsors...')
        for sponsor_name in sponsors:
            if not Sponsor.objects.filter(name=sponsor_name).exists():
                s = Sponsor(name=sponsor_name)
                s.save()
            Sponsorship(rider=Rider.objects.get(pk=rider_id), sponsor=Sponsor.objects.get(name=sponsor_name), main=main).save()
            if main:
                main = False

    @staticmethod
    def scrapeAllSponsors():
        riders = Rider.objects.all()
        n = riders.count()
        for rider in riders:
            print('-----')
            print(f'Scraping {n}th rider:', rider.name)
            rider_id = rider.id
            Sponsorship.scrapeSponsors(rider_id)

