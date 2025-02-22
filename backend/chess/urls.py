from django.urls import path, include

from . import apiviews

urlpatterns = [
    path('', apiviews.get_games, name='get-games'),
]