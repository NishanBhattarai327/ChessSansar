from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chess/$', consumers.ChessRoomConsumer.as_asgi()),   # consumer for showing availabe room
    re_path(r"ws/chess/(?P<game_id>\w+)/$", consumers.ChessConsumer.as_asgi()),
]