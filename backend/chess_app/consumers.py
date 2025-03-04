# consumers.py
from channels.generic.websocket import WebsocketConsumer
from .models import Game, Clock, Move
import json
from asgiref.sync import async_to_sync
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
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'connected',
                        'player': {
                            'user': user.username
                        }
                    }
                }))
            else:
                self.close()
        else:
            print(f"no user and received gameid = {self.game_id}")
            self.close()
    
    def disconnect(self, close_code):
        if self.room_group_name:
            if "user" in self.scope:
                user = self.scope["user"]
                if Game.objects.filter(room_id=self.game_id).exists():
                    game = Game.objects.get(room_id=self.game_id)
                    if game is not None:
                        game.status = "waiting"
                        game.save()
                        print(f"change => game : {game.room_id}  status to {game.status}")
            async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
    
    def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            user = self.scope['user']
        except Exception as e:
            self.send(text_data=json.dumps({
                'game': {},
                'message': {
                    'type': 'only_me',
                    'info': 'invalid',
                    'error': f'{e}',
                    'player': {}
                } 
            }))
            return
        
        if action == 'create_game':
            base = data.get('base', None)
            increment = data.get('increment', None)
            if base is None or increment is None:
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'provide base and increment',
                        'player': {}
                    } 
                }))
                return
            
            # Create a new game
            if not Game.objects.filter(room_id=self.game_id).exists():
                # Todo : ask user of color of player 1 (defualt is white)
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
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'Game already exists',
                        'player': {}
                    }
                }))
                return
            
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            # Also send message to available room group
            async_to_sync(self.channel_layer.group_send)(
                'available_games',
                {
                    'type': 'game.update',
                    'game': {
                        'game_id': self.game_id,
                        'player1': game.player1.username,
                        'player1_color': game.player1_color,
                        'player2_color': game.player2_color,
                        'current_turn': game.current_turn,
                    },
                    'message': {
                        'type': 'all',
                        'info': 'available',
                        'player': {
                            'user': user.username
                        }
                    }
                }
            )
            self.send(text_data=json.dumps({
                'game': {
                    'game_id': self.game_id,
                    'base': clock.total_time,
                    'increment': clock.incremental_time,
                    'player1': user.username,
                    'player1_color': game.player1_color,
                    'player2_color': game.player2_color
                },
                'message': {
                    'type': 'only_me',
                    'info': 'created',
                    'player': {
                        'user': user.username,
                        'color': game.player1_color,
                    }
                }
            }))

        
        elif action == 'join_game':
            print(f"{user.username} : action: join_game")
            try:
                game = Game.objects.get(room_id=self.game_id)
            except Game.DoesNotExist:
                game = None
            if game is None:
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'Game does not exists',
                        'player': {}
                    }
                }))
                return

            # if game is not in waiting state return
            if game.status != "waiting":
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'Game is either end or active!!',
                        'player': {}
                    }
                }))
                return
            
            # reconnect the players if game is still in waiting status
            if game.player1 == user or game.player2 == user:
                async_to_sync(self.channel_layer.group_add)(
                    self.room_group_name,
                    self.channel_name
                )
                color = game.player1_color if game.player1 == user else game.player2_color
            
                # Broadcast the join info to the group
                # Get all moves for this game
                moves = list(Move.objects.filter(game=game).values('move', 'played_at'))
                # Convert datetime to string format
                for move in moves:
                    move['played_at'] = move['played_at'].isoformat() if move['played_at'] else None

                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'game.send',
                        'game': {
                            'game_id': self.game_id,
                            'fen': game.fen,
                            'player1': game.player1.username,
                            'player1_color': game.player1_color,
                            'player2': game.player2.username if game.player2 else 'null',
                            'player2_color': game.player2_color,
                            'current_turn': game.current_turn,
                            'moves': moves
                        },
                        'message': {
                            'type': 'both',
                            'info': 'reconnected',
                            'player': {
                                'user': user.username,
                                'color': color
                            }
                        }
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
                            'player1_color': game.player1_color,
                            'player2': game.player2.username,
                            'player2_color': game.player2_color,
                            'current_turn': game.current_turn,
                            'status': game.status
                        },
                        'message': {
                            'type': 'both',
                            'info': 'joined',
                            'player': {
                                'user': user.username,
                                'color': game.player2_color
                            }
                        }
                    }
                )
            else:
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'Game is full',
                        'player': {}
                    }
                }))
        

        elif action == 'make_move':
            print(f"{user.username} : action: make_move")
            try:
                game = Game.objects.get(room_id=self.game_id)
            except Game.DoesNotExist:
                game = None
            if game is None:
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'Game does not exists',
                        'player': {}
                    }
                }))
                return

            if user != game.player1 and user != game.player2:
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'You are not a player in this game',
                        'player': {}
                    }
                }))
                return

            turn = game.current_turn
            if (turn == "player1" and user == game.player2) or (turn == "player2" and user == game.player1):
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'not your turn',
                        'player': {}
                    }
                }))
                return
            
            if "move" not in data:
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': 'no move to make',
                        'player': {}
                    }
                }))
                return

            try:
                move = data['move']
                print(f'{user.username} :: make_move :: move : {move}')
                game = Game.objects.get(room_id=self.game_id)
                color = game.player1_color if game.player1 == user else game.player2_color   # color of the move maker
                
                if game.status == 'ended':
                    self.send(text_data=json.dumps({
                        'game': {},
                        'message': {
                            'type': 'only_me',
                            'info': 'invalid',
                            'error': "game has already ended",
                            'player': {
                                'user': user.username,
                                'color': color
                            }
                        }
                    }))
                    return

                board = chess.Board(fen=game.fen)
                chess_move = chess.Move.from_uci(move)
                if chess_move not in board.legal_moves:
                    self.send(text_data=json.dumps({
                        'game': {},
                        'message': {
                            'type': 'only_me',
                            'info': 'invalid',
                            'error': "illegal move",
                            'player': {
                                'user': user.username,
                                'color': color
                            }
                        }
                    }))
                    return
                
                board.push(chess_move)
                move_model = Move.objects.create(
                    game=game,
                    move=move
                )

                # add new FEN to game and check if game if over or not
                game.fen = board.fen()
                game.current_turn = "player2" if user == game.player1 else "player1"
                
                outcome = board.outcome()
                if outcome:
                    over_type = ''
                    winner = ''
                    if outcome.winner == chess.WHITE:
                        print("white won")
                        over_type = 'checkmate'
                        winner = 'player1' if game.player1_color == 'white' else 'player2'

                    elif outcome.winner == chess.BLACK:
                        over_type = 'checkmate'
                        winner = 'player1' if game.player1_color == 'black' else 'player2'
                        print("black won")

                    else:
                        over_type = 'draw'
                        print("draw")
                    game.status = 'ended'
                    game.over_type = over_type
                    game.winner = winner
                game.save()

                # Broadcast the move to the group
                async_to_sync(self.channel_layer.group_send)(
                    self.room_group_name,
                    {
                        'type': 'game.send',
                        'game': {
                            'game_id': self.game_id,
                            'fen': game.fen,
                            'move': move,
                            'player1': game.player1.username,
                            'player1_color': game.player1_color,
                            'player2': game.player2.username,
                            'player2_color': game.player2_color,
                            'current_turn': game.current_turn,
                            'status': game.status,
                            'winner': game.winner,
                            'over_type': game.over_type
                        },
                        'message': {
                            'type': 'both',
                            'info': 'moved',
                            'player': {
                                'user': user.username,
                                'color': color
                            }
                        }
                    }
                )
            except Exception as e:
                self.send(text_data=json.dumps({
                    'game': {},
                    'message': {
                        'type': 'only_me',
                        'info': 'invalid',
                        'error': str(e),
                        'player': {
                            'user': user.username
                        }
                    }
                }))

    def game_send(self, event):
        message = event['message']
        game = event['game']
        self.send(text_data=json.dumps({
            "message": message,
            "game": game
        }))



class ChessRoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = 'available_games'
        user = self.scope['user']

        if user.username:
            print(f"Connected to room {self.room_group_name} as {user.username}")

            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name,
                self.channel_name
            )
            self.accept()
            
            # Send current available games on connect
            available_games = Game.objects.filter(status='waiting')
            games_list = [{
                'game_id': game.room_id,
                'player1': game.player1.username,
            } for game in available_games]

            self.send(text_data=json.dumps({ 
                'games': games_list,
                'message': {
                    'type': 'only_me',
                    'info': 'connected',
                    'player': {
                        'user': user.username
                    }
                }
            }))
    
    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
    
    def receive(self, text_data):
        pass

    def game_update(self, event):
        """Handle game updates from database"""
        self.send(text_data=json.dumps({
            'game': event['game'],
            'message': event['message']
        }))