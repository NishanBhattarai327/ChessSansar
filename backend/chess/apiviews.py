from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import Game, Move
from .serializers import GameSerializer

@api_view(['GET'])
def get_games(request):
    games = Game.objects.all()
    serializer = GameSerializer(games, many=True)
    return Response(serializer.data)