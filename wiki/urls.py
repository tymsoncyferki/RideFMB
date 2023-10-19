from django.urls import *
from . import views

app_name = 'wiki'
urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('rider/<int:rider_id>/<slug:slug>', views.rider, name='rider'),
    path('event/<int:event_id>/<slug:slug>', views.event, name='event'),
    path('ranking/<int:page_idx>', views.ranking, name='ranking'),
    path('riders', views.riders, name='riders'),
    path('events', views.events, name='events'),
    path('schedule/<int:year>', views.schedule, name='schedule'),
    path('help', views.help_view, name='help'),
    path('contact', views.contact, name='contact'),
    path('contact/success', views.success, name='success'),
    path('about', views.about, name='about'),
    path('markdownx/', include('markdownx.urls')),
    path('registration/login', views.login_view, name='login'),
    path('registration/logout', views.logout_view, name='logout'),
    path('account', views.account, name='account')
]
