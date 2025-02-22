from rest_framework import serializers
from .models import Game, Move, Clock

class GameSerializer(serializers.ModelSerializer):
    game_moves = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='move'
    )
    game_clock = serializers.SlugRelatedField(
        read_only=True,
        slug_field='started_at'
    )

    class Meta:
        model = Game
        fields = ['id', 'player1', 'player2', 'current_turn', 'fen', 'status', 'winner', 'over_type', 'format', 'game_moves', 'game_clock']
