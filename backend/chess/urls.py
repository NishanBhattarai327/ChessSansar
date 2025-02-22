from django.urls import path, include

from . import apiviews

urlpatterns = [
    path('', apiviews.home, name='home'),
]