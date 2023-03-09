from django.urls import *
from . import views

app_name = 'wiki'
urlpatterns = [
    path('', views.index, name='index'),
    path('search', views.search, name='search'),
    path('rider/<int:rider_id>/<slug:slug>', views.rider, name='rider'),
    path('event/<int:event_id>/<slug:slug>', views.event, name='event')
]