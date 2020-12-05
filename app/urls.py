from django.urls import path
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/eplfantasy/2020/', permanent=False), name='index'),
    path('eplfantasy/2020/', views.index, name='eplfantasy20'),
]