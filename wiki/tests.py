from django.test import TestCase
from .models import *

class RiderTestCase(TestCase):

    def setUp(self):
        Event.objects.create(name="UFS Slopestyle - Stop 3 (M/W) 2023", date='2023-05-24')
        Event.objects.create(name="UFS Slopestyle - Stop 3 (M) 2023", date='2022-05-24')

    def tearDown(self):
        Event.objects.all().delete()
        Rider.objects.all().delete()

    def test_getMainSponsor(self):
        pass


class EventTestCase(TestCase):

    def setUp(self):
        Event.objects.create(name="UFS Slopestyle - Stop 3 (M/W) 2023", date='2023-05-24')
        Event.objects.create(name="UFS Slopestyle - Stop 3 (M) 2023", date='2022-05-24')

    def tearDown(self):
        Event.objects.all().delete()

    def test_cleanName(self):
        event = Event.objects.get(name="UFS Slopestyle - Stop 3 (M/W) 2023")
        clean_name = event.cleanName()
        self.assertEqual(clean_name, 'UFS Slopestyle - Stop 3')

    def test_displayName(self):
        event_mw = Event.objects.get(name="UFS Slopestyle - Stop 3 (M/W) 2023")
        event_m = Event.objects.get(name="UFS Slopestyle - Stop 3 (M) 2023")
        display_name_mw = event_mw.displayName()
        display_name_m = event_m.displayName()
        self.assertEqual(display_name_mw, 'UFS Slopestyle - Stop 3 (M/W)')
        self.assertEqual(display_name_m, 'UFS Slopestyle - Stop 3')

    def test_fixStatus(self):
        event_u = Event.objects.get(name="UFS Slopestyle - Stop 3 (M/W) 2023")
        event_c = Event.objects.get(name="UFS Slopestyle - Stop 3 (M) 2023")
        event_u.fixStatus()
        event_c.fixStatus()
        self.assertEqual(event_u.status, 'Upcoming')
        self.assertEqual(event_c.status, 'Canceled')


class CountryTestCase(TestCase):

    def setUp(self):
        Country.objects.create(shortname='POL')
        Country.objects.create(shortname='HUN')
        Country.objects.create(shortname='ISR')

    def test_createCountries(self):
        Country.createCountries()

        poland = Country.objects.get(shortname='POL')
        hungary = Country.objects.get(shortname='HUN')
        israel = Country.objects.get(shortname='ISR')

        self.assertEqual(poland.isocode, 'PL')
        self.assertEqual(poland.name, 'Poland')
        self.assertEqual(hungary.isocode, 'HU')
        self.assertEqual(hungary.name, 'Hungary')
        self.assertEqual(israel.isocode, 'IL')
        self.assertEqual(israel.name, 'Israel')


class SeriesTestCase(TestCase):

    def setUp(self):
        Event.objects.create(name="Dirt Wars - Stop 2 (M/W)", date='2023-05-24')
        Event.objects.create(name="Dirt Wars - Stop 3", date='2023-05-24')
        Event.objects.create(name="Dirt Wars - Stop 5", date='2023-05-24')
        Series.objects.create(name="Dirt Wars - Stop 2")
        Series.objects.create(name="Dirt Wars - Stop 3")
        Series.objects.create(name="Dirt Wars - Stop 5")

    def test_fixSeries(self):
        event_1 = Event.objects.get(name="Dirt Wars - Stop 2 (M/W)")
        event_2 = Event.objects.get(name="Dirt Wars - Stop 3")
        event_3 = Event.objects.get(name="Dirt Wars - Stop 5")
        event_1.series = Series.objects.get(name=event_1.cleanName())
        event_2.series = Series.objects.get(name=event_2.cleanName())
        event_3.series = Series.objects.get(name=event_3.cleanName())

        Series.fixSeries('Dirt Wars')

        series = Series.objects.get(name="Dirt Wars")
        event_1 = Event.objects.get(name="Dirt Wars - Stop 2 (M/W)")
        event_2 = Event.objects.get(name="Dirt Wars - Stop 3")
        event_3 = Event.objects.get(name="Dirt Wars - Stop 5")

        self.assertEqual(series.event_set.count(), 3)
        self.assertEqual(event_1.series, series)
        self.assertEqual(event_1.series, event_2.series)
        self.assertEqual(event_3.series.name, 'Dirt Wars')

