from django.test import TestCase
from .models import *
from django.urls import reverse
from django.contrib.auth.models import User


class RiderTestCase(TestCase):

    def setUp(self):
        ufs = Event.objects.create(name="UFS Slopestyle - Stop 3 (M/W) 2023", date='2023-05-24')
        kazz = Event.objects.create(name="Kazoora Bikefest", date='2022-05-24')
        ns = Sponsor.objects.create(name='NS Bikes')
        red = Sponsor.objects.create(name='Red Bull')
        r = Rider.objects.create(name="Sebastian Majder")
        Participation.objects.create(rider=r, event=ufs, points=200, rank=1)
        Participation.objects.create(rider=r, event=kazz, points=100, rank=3)
        Sponsorship.objects.create(rider=r, sponsor=ns, main=True)
        Sponsorship.objects.create(rider=r, sponsor=red, main=True)

    def test_getMainSponsor(self):
        r = Rider.objects.get(name="Sebastian Majder")
        self.assertEqual(r.getMainSponsor(), 'NS Bikes')

    def test_updateMedals(self):
        r = Rider.objects.get(name="Sebastian Majder")
        self.assertEqual(r.medal, 0)
        r.updateMedals()
        self.assertEqual(r.medal, 2)
        self.assertEqual(r.gold, 1)
        self.assertEqual(r.bronze, 1)
        self.assertEqual(r.alltime_points, 300)


class EventTestCase(TestCase):

    def setUp(self):
        Event.objects.create(name="UFS Slopestyle - Stop 3 (M/W) 2023", date='2023-05-24')
        Event.objects.create(name="UFS Slopestyle - Stop 3 (M) 2023", date='2022-05-24')

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

    def tearDown(self):
        Event.objects.all().delete()


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


class LoginViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_login_valid(self):
        response = self.client.post(reverse('wiki:login'), {'uname': 'testuser', 'psw': 'testpassword'})
        self.assertRedirects(response, reverse('wiki:account'))

    def test_login_invalid(self):
        response = self.client.post(reverse('wiki:login'), {'uname': 'testuser', 'psw': 'wrongpassword'})
        self.assertTemplateUsed(response, 'wiki/registration/login.html')
        self.assertContains(response, "Wrong username or password")

    def test_login_authenticated(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('wiki:login'))
        self.assertRedirects(response, reverse('wiki:account'))

    def test_login_unauthenticated(self):
        response = self.client.get(reverse('wiki:login'))
        self.assertTemplateUsed(response, 'wiki/registration/login.html')

    def tearDown(self):
        self.user.delete()


class DeleteViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('wiki:delete')

    def test_delete_authenticated(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'wiki/registration/delete.html')

    def test_delete_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('wiki:login'))

    def test_delete_authenticated_post(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(self.url, {'check': 'yes'})
        self.assertRedirects(response, reverse('wiki:login'))
        with self.assertRaises(User.DoesNotExist):
            self.user.refresh_from_db()

    def tearDown(self):
        self.user.delete()


class PasswordViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('wiki:password')

    def test_password_authenticated(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'wiki/registration/password.html')

    def test_password_authenticated_post_correct(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(self.url, {'psw': 'testpassword', 'npsw': 'newpassword'})
        self.assertRedirects(response, reverse('wiki:success'))
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('newpassword'))

    def test_password_authenticated_post_incorrect(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(self.url, {'psw': 'wrongpassword', 'npsw': 'newpassword'})
        self.assertTemplateUsed(response, 'wiki/registration/password.html')
        user = User.objects.get(username='testuser')
        self.assertTrue(user.check_password('testpassword'))

    def test_password_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('wiki:login'))

    def tearDown(self):
        self.user.delete()


class RegisterViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('wiki:register')

    def test_register_authenticated(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('wiki:account'))

    def test_register_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'wiki/registration/register.html')

    def test_register_registration(self):
        data = {
            'email': 'newuser@example.com',
            'uname': 'newuser',
            'psw': 'password123',
            'psw2': 'password123',
        }

        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('wiki:account'))

        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.email, 'newuser@example.com')

    def test_register_email(self):
        User.objects.create_user(username='existinguser', password='existingpassword', email='existing@example.com')

        data = {
            'email': 'existing@example.com',
            'uname': 'newuser',
            'psw': 'password123',
            'psw2': 'password123',
        }

        response = self.client.post(self.url, data)
        self.assertTemplateUsed(response, 'wiki/registration/register.html')

    def test_register_username(self):
        User.objects.create_user(username='existinguser', password='existingpassword', email='existing@example.com')

        data = {
            'email': 'newuser@example.com',
            'uname': 'existinguser',
            'psw': 'password123',
            'psw2': 'password123',
        }

        response = self.client.post(self.url, data)
        self.assertTemplateUsed(response, 'wiki/registration/register.html')

    def test_register_password(self):
        data = {
            'email': 'newuser@example.com',
            'uname': 'newuser',
            'psw': 'password123',
            'psw2': 'password456',
        }

        response = self.client.post(self.url, data)
        self.assertTemplateUsed(response, 'wiki/registration/register.html')

    def tearDown(self):
        User.objects.filter(username='newuser').delete()

