from django.urls import *
from . import views

app_name = 'wiki'
urlpatterns = [
    path('', views.index, name='index')
]