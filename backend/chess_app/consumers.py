# consumers.py
from channels.generic.websocket import WebsocketConsumer
from .models import Game, Clock, Move
import json
from asgiref.sync import async_to_sync

import sys
import site
import chess


class ChessConsumer(WebsocketConsumer):
    def connect(self):
        self.game_id = self.scope['url_route']['kwargs'].get('game_id')
        self.room_group_name = f'game_{self.game_id}' if self.game_id else None
        user = self.scope['user']

        if user.username:
            print(f"Connected to game {self.game_id} as {user.username}")
 
            if self.room_group_name:
                # Join the game group
                async_to_sync(self.channel_layer.group_add)(
                    self.room_group_name,
                    self.channel_name
                )
                self.accept()
                self.send(text_data=json.dumps({
                    'message': 'Connected',
                    'username': user.username
                }))
            else:
                self.close()
        else:
            print(f"no user and received gameid = {self.game_id}")
            self.close()
    
    def disconnect(self, close_code):
        if self.room_group_name:
            async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
    
    def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        user = self.scope['user']
        
        if action == 'create_game':
            base = data.get('base', None)
            increment = data.get('increment', None)
            if base is None or increment is None:
                self.send(text_data=json.dumps({
                    'message': 'provide base and increment'
                }))
                return
            
            # Create a new game
            if not Game.objects.filter(room_id=self.game_id).exists():
                game = Game.objects.create(
                    player1=user,
                    room_id=self.game_id,
                    fen=chess.Board().fen(),
                    status="waiting"
                )
                clock = Clock.objects.create(
                    game=game,
                    total_time=base,
                    incremental_time=increment,
                    clock1=base,
                    clock2=base
                )
            else:
                self.send(text_data=json.dumps({
                    'message': 'Game already exists'
                }))
                return
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.send(text_data=json.dumps({
                'message': 'Game created',
                'game_id': self.game_id,
                'clock': clock.total_time,
                'username': user.username
            }))
        elif action == 'join_game':
            game = Game.objects.get(room_id=self.game_id)
            if game is None:
                self.send(text_data=json.dumps({
                    'message': 'Game does not exists'
                }))
                return

            # if game is not in waiting state return
            if game.status != "waiting":
                self.send(text_data=json.dumps({
                    'message': 'Game is either end or active!!'
                }))
                return
            
            # reconnect the players if game is still in waiting status
            if game.player1 == user or game.player2 == user:
                async_to_sync(self.channel_layer.group_add)(
                    self.room_group_name,
                    self.channel_name
                )
                # Broadcast the join info to the group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'game.send',
                        'game': {
                            'game_id': self.game_id,
                            'player1': game.player1.username,
                            'player2': game.player2.username,
                            'current_turn': game.current_turn
                        },
                        'message': 'reconnected'
                    }
                )
                return


            if game.player2 is None:
                game.player2 = user
                game.status = "active"
                game.save()
                async_to_sync(self.channel_layer.group_add)(
                    self.room_group_name,
                    self.channel_name
                )
                # Broadcast the join info to the group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'game.send',
                        'game': {
                            'game_id': self.game_id,
                            'player1': game.player1.username,
                            'player2': game.player2.username,
                            'current_turn': game.current_turn,
                        },
                        'message': 'Joined game'
                    }
                )
            else:
                self.send(text_data=json.dumps({
                    'message': 'Game is full'
                }))
        elif action == 'make_move':
            game = Game.objects.get(id=self.game_id)
            if user != game.player1 and user != game.player2:
                self.send(text_data=json.dumps({
                    'message': 'You are not a player in this game',
                    "username": user.username
                }))
                return
            move = data['move']
            game = Game.objects.get(id=self.game_id)
            board = chess.Board(fen=game.fen)
            try:
                board.push(chess.Move.from_uci(move))
                # Save new FEN and broadcast update
                game.fen = board.fen()
                game.current_turn = "player2" if user == game.player1 else "player1"
                game.save()

                # Broadcast the move to the group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'game.update',
                        'move': move,
                        'fen': game.fen,
                        'current_turn': game.current_turn
                    }
                )
            except Exception as e:
                self.send(text_data=json.dumps({
                    'message': str(e)
                }))

    def game_send(self, event):
        message = event['message']
        game = event['game']
        self.send(text_data=json.dumps({
            "message": message,
            "game": game
        }))

    def game_update(self, event):
        # Send updates to all clients in the group
        self.send(text_data=json.dumps(event))