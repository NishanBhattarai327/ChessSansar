from django.db import models
import datetime
from django.contrib.auth.models import User

class Game(models.Model):
    room_id = models.CharField(max_length=24, primary_key=True, blank=True)

    player1 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='player1')
    player1_color = models.CharField(max_length=10, default="white")

    player2 = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='player2')
    player2_color = models.CharField(max_length=10, default="black")
    
    # infomation about where the players are connected or not to the game
    PLAYER_STATUS_CHOICES = [('connected', 'Connected'), ('disconnected', 'Disconnected')]
    player1_status = models.CharField(max_length=16, choices=PLAYER_STATUS_CHOICES, default='disconnected')
    player2_status = models.CharField(max_length=16, choices=PLAYER_STATUS_CHOICES, default='disconnected')

    TURN_CHOICES = [('player1', 'Player 1'), ('player2', 'Player 2')]
    current_turn = models.CharField(max_length=64, choices=TURN_CHOICES, default='player1')

    fen = models.CharField(max_length=100, default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')  # Initial FEN/ Board
    STATUS_CHOICES = [('waiting', 'Waiting'), ('active', 'Active'), ('ended', 'Ended')]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')

    winner = models.CharField(max_length=64, choices=TURN_CHOICES, null=True, blank=True)

    OVER_TYPES = [('draw', 'Draw'), ('resign', 'Resign'), ('checkmate', 'Checkmate')]
    over_type = models.CharField(max_length=20, null=True, blank=True, choices=OVER_TYPES)
    
    # time
    FORMAT_CHOICES = [('classic', 'Classic'), ('rapid', 'Rapid'), ('bliz', 'Bliz'), ('bullet', 'Bullet'), ('custom', 'Custom')]
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='rapid')
    
    def __str__(self):
        return f"Game {self.room_id} between {self.player1} and {self.player2} of format {self.format}"

class Clock(models.Model):
    DEFAULT_TOTAL_TIME = 15 * 60 * 1000  # 15 minutes in milliseconds
    DEFAULT_INCREMENTAL_TIME = 0  # 0 seconds

    game = models.OneToOneField(
        Game,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='game_clock'
    )

    started_at = models.DateTimeField(auto_now_add=True)
    total_time = models.IntegerField(default=DEFAULT_TOTAL_TIME, help_text="Total time in milliseconds")
    incremental_time = models.IntegerField(default=DEFAULT_INCREMENTAL_TIME, help_text="Incremental time in milliseconds")

    clock1 = models.IntegerField(default=DEFAULT_TOTAL_TIME, help_text="Player1 remaining time in ms")  # Clock for player1
    clock2 = models.IntegerField(default=DEFAULT_TOTAL_TIME, help_text="Player2 remaining time in ms")  # Clock for player2

    def __str__(self):
        return f"Clock {self.total_time/(1000*60)}mins|+{self.incremental_time/1000}secs ({self.started_at}) game:"
    
class Move(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='game_moves')
    move = models.CharField(max_length=10, help_text="move in SAN")  # e.g., "e4", "Nf3"
    played_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Played move {self.move} in game {self.game.room_id}"