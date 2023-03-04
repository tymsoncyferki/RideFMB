from django.urls import *
from . import views

app_name = 'wiki'
urlpatterns = [
    path('', views.index, name='index'),
    path('search', views.search, name='search'),
    path('rider/<str:rider_name>/<int:rider_id>', views.rider, name='rider')
]