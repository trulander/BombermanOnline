import json
import uuid
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import eventlet
from game.game import Game
from game.player import Player

app = Flask(__name__, static_folder='../dist', template_folder='../dist')
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Games dictionary to store active games
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)
    # Remove player from game if they were in one
    for game_id, game in list(games.items()):
        if request.sid in game.players:
            game.remove_player(request.sid)
            # If game is empty, remove it
            if len(game.players) == 0:
                del games[game_id]
            else:
                # Notify other players
                emit('player_disconnected', {'player_id': request.sid}, room=game_id)

@socketio.on('create_game')
def handle_create_game(data):
    # Принимаем data как аргумент, даже если не используем
    game_id = str(uuid.uuid4())
    games[game_id] = Game()
    return {'game_id': game_id}

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data['game_id']
    if game_id not in games:
        return {'success': False, 'message': 'Game not found'}
    
    player = Player(request.sid)
    success = games[game_id].add_player(player)
    
    if success:
        # Join the socket room for this game
        join_room(game_id)
        # Send initial game state
        game_state = games[game_id].get_state()
        return {
            'success': True, 
            'player_id': request.sid,
            'game_state': game_state
        }
    else:
        return {'success': False, 'message': 'Game is full'}

@socketio.on('input')
def handle_input(data):
    game_id = data['game_id']
    inputs = data['inputs']
    
    if game_id in games:
        game = games[game_id]
        player = game.get_player(request.sid)
        
        if player:
            player.set_inputs(inputs)
            
            # Process one game step
            updated_state = game.update()
            
            # Broadcast updated game state to all players in the game
            emit('game_update', updated_state, room=game_id)

@socketio.on('place_bomb')
def handle_place_bomb(data):
    game_id = data['game_id']
    
    if game_id in games:
        game = games[game_id]
        player = game.get_player(request.sid)
        
        if player:
            success = game.place_bomb(player)
            if success:
                # Broadcast bomb placement
                updated_state = game.get_state()
                emit('game_update', updated_state, room=game_id)

def game_loop():
    """Background task that updates games and sends updates to clients"""
    while True:
        for game_id, game in list(games.items()):
            if game.is_active():
                updated_state = game.update()
                socketio.emit('game_update', updated_state, room=game_id)
            else:
                # Game is over, clean up
                for player_id in game.players:
                    socketio.emit('game_over', room=player_id)
                del games[game_id]
        eventlet.sleep(0.033)  # ~30 FPS

if __name__ == '__main__':
    # Start background task for game loop
    socketio.start_background_task(game_loop)
    # Start server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
