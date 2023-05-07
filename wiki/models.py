import pycountry
from django.core.exceptions import *
from django.db import models
from markdownx.models import MarkdownxField
import re
import shutil

from wiki.utils.countries import country_codes
from wiki.utils.patterns import series_args, series_names, partners_args


class Rider(models.Model):
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=150, default='rider_name')
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    birth = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=20, default='Unknown', blank=True)
    description = MarkdownxField(blank=True)
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
        try:
            sponsor = self.sponsorship_set.filter(main=True)[0].sponsor.name
        except IndexError:
            sponsor = ''
        return sponsor

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


class Source(models.Model):
    link = models.CharField(max_length=255, default='#')
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE)


class Event(models.Model):
    name = models.CharField(max_length=150, blank=True)
    slug = models.SlugField(max_length=150, default='event_name')
    date = models.DateField(null=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.ForeignKey('Country', on_delete=models.SET_NULL, null=True)
    category = models.CharField(max_length=100, blank=True)
    discipline = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='Upcoming')
    series = models.ForeignKey('Series', on_delete=models.SET_NULL, null=True)
    prize = models.CharField(max_length=255, blank=True)
    website = models.CharField(max_length=255, blank=True)
    partners = models.ManyToManyField('Partner', through='Partnership')
    riders = models.ManyToManyField('Rider', through='Participation')

    def __str__(self):
        return f"{self.name}, {self.date.year}"

    def completed(self):
        if self.status == 'Completed':
            return True
        else:
            return False

    def cleanName(self):
        """ Drops brackets and dates"""
        string = self.name
        index = string.rfind('(')
        if index != -1:
            string = string[:index]
        pattern = r'\b\d{4}\b'
        string = re.sub(pattern, '', string)
        return string.strip()

    def displayName(self):
        string = self.name
        index = string.rfind('(M)')
        if index != -1:
            string = string[:index]
        pattern = r'\b\d{4}\b'
        string = re.sub(pattern, '', string)
        return string.strip()

    def year(self):
        return self.date.year

    @staticmethod
    def fixEventWebsite():
        # TODO: fix links
        pass


class Sponsor(models.Model):
    name = models.CharField(max_length=150, blank=True)
    riders = models.ManyToManyField('Rider', through='Sponsorship')

    def __str__(self):
        name = str(self.name)
        return name

    def strID(self):
        return str(self.id)


class Participation(models.Model):
    rider = models.ForeignKey('Rider', on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    rank = models.IntegerField(default=None, blank=True)
    points = models.FloatField(default=0, blank=True)
    run1 = models.FloatField(default=0, blank=True)
    run2 = models.FloatField(default=0, blank=True)

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

    def strID(self):
        return str(self.id)

    def hasMultipleEvents(self):
        return self.event_set.count() > 1

    @staticmethod
    def fixSeries(arg, new_name=None):
        if not new_name:
            new_name = arg
        arg_series = Series.objects.filter(name__icontains=arg)
        s = Series(name=new_name)
        s.save()
        for series in arg_series:
            print('Series:', series)
            series_events = series.event_set.all()
            for event in series_events:
                print('Event:', event)
                event.series = s
                event.save()
            series.delete()

    @staticmethod
    def seriesNames(pattern, name):
        print('pattern: ' + pattern + ', name: ' + name)
        s = Series.objects.filter(name__icontains=pattern)
        try:
            s = s[0]
        except (IndexError, AttributeError):
            print('No results')
            return
        print(s.name)
        s.name = name
        s.save()


class Partner(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name

    def strID(self):
        return str(self.id)

    @staticmethod
    def fixPartners(arg):
        """
        Fixes same partners but written differently
        arg - pattern (string) that all partners contain
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


class AppData(models.Model):
    lastUpdate = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk and AppData.objects.exists():
            # if you'll not check for self.pk
            # then error will also be raised in update of exists model
            raise ValidationError('There can be only one AppData instance')
        return super(AppData, self).save(*args, **kwargs)


def getID(url):
    """ Extracts ID from url """
    id_index = url.index('=') + 1
    return url[id_index:]


def backupDatabase():
    shutil.copy2('wiki/static/wiki/db.sqlite3', 'wiki/static/wiki/backup.sqlite3')


def cleanDatabase():
    print('Cleaning Series')
    # Joins split series
    for arg in series_args:
        Series.fixSeries(arg)
    # Renames series
    for mapping in series_names:
        Series.seriesNames(mapping[0], mapping[1])
    # Deletes blank partner
    try:
        p = Partner.objects.filter(name='')[0]
        p.delete()
    except IndexError:
        pass


def allocateSex():
    riders = Rider.objects.all()
    for rider in riders:
        print('Rider:', rider.name)
        events = rider.event_set.all()
        for event in events:
            if '(W)' in event.name or event.name.lower().find('women') != -1 or event.id == 380:
                rider.sex = 'Female'
                rider.save()
                break
            if '(M)' in event.name:
                rider.sex = 'Male'
                rider.save()
                break
        if rider.sex == 'Unknown':
            for eventt in events:
                if eventt.name.find('(') == -1 and eventt.name.find('M%W') == -1:
                    rider.sex = 'Male'
                    rider.save()
                    break
        if rider.sex == 'Unknown':
            print('Sex unknown')
        else:
            print('Sex allocated')


def changeSex(riders_list, male=False):
    for rider_id in riders_list:
        rider = Rider.objects.get(id=rider_id)
        print(rider.name)
        if male:
            rider.sex = 'Male'
        else:
            rider.sex = 'Female'
        rider.save()
