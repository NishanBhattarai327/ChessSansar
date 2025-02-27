from rest_framework import serializers
from .models import Game, Move, Clock

class GameSerializer(serializers.ModelSerializer):
    player1 = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username"
    )
    player2 = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username"
    )
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
        fields = ['room_id', 'player1', 'player1_color', 'player2', 'player2_color', 'current_turn', 'fen', 'status', 'winner', 'over_type', 'format', 'game_moves', 'game_clock']
