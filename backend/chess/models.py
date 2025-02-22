from django.db import models
import datetime
from django.contrib.auth.models import User

class Clock(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    total_time = models.TimeField(default=datetime.timedelta(minutes=15))
    incremental_time = models.TimeField(default=datetime.timedelta(seconds=0))
    clock1 = models.TimeField(default=total_time)  # Clock for player1
    clock2 = models.TimeField(default=total_time)  # Clock for player2


class Game(models.Model):
    player1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='player1_games')
    player2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='player2_games')

    TURN_CHOICES = [('player1', player1), ('player2', player2)]
    current_turn = models.CharField(max_length=64, choices=TURN_CHOICES, default='player1')

    fen = models.CharField(max_length=100, default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')  # Initial FEN/ Board
    STATUS_CHOICES = [('waiting', 'Waiting'), ('active', 'Active'), ('ended', 'Ended')]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='won_games')
    OVER_TYPES = [('draw', 'Draw'), ('resign', 'Resign'), ('checkmate', 'Checkmate')]
    over_type = models.CharField(max_length=20, null=True, choices=OVER_TYPES)
    
    # time
    FORMAT_CHOICES = [('classic', 'Classic'), ('rapid', 'Rapid'), ('bliz', 'Bliz'), ('bullet', 'Bullet'), ('custom', 'Custom')]
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='rapid')

    clock = models.OneToOneField(
        Clock,
        on_delete=models.PROTECT,
        related_name='game_clock',
        null=True
    )
    
    def __str__(self):
        return f"Game {self.id}"

    
class Move(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='game_moves')
    move = models.CharField(max_length=10, help_text="move in SAN")  # e.g., "e4", "Nf3"
    played_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Played move {self.move} in game {self.game.id}"